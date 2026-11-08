"""Backfill Localize translations without the browser or newsletter side effects."""
import json
import sys
import re
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.models import Locale, Page, Site
from wagtail_localize.machine_translators import get_machine_translator
from wagtail_localize.models import StringTranslation, Translation, TranslationSource
from wagtail_localize.segments import StringSegmentValue
from wagtail_localize.segments.extract import extract_segments


LEAKED_MARKUP = ('&lt;b&gt;', '&lt;/b&gt;', '&lt;br')


def is_bad_translation(data):
    """Prompt preambles, `N:` paragraph numbers (1–3 digits, so a leading year is fine) and tags the model escaped into text."""
    return ('translated paragraphs' in data.lower()
            or bool(re.search(r'(^|<br/?>|\n)\s*\d{1,3}:', data))
            or any(marker in data for marker in LEAKED_MARKUP))


def pending_strings(page, locale):
    """Match strings AND contexts, as the admin does; extract without writing for dry runs."""
    existing = {
        (item.context.path, item.translation_of.data): item
        for item in StringTranslation.objects.filter(
            locale=locale, context__object_id=page.translation_key,
            translation_of__locale=page.locale,
        ).select_related('context', 'translation_of')
    }
    pending = defaultdict(list)
    bad_ids = []
    for segment in extract_segments(page):
        if not isinstance(segment, StringSegmentValue):
            continue
        stored = existing.get((segment.path, segment.string.data))
        if stored and not is_bad_translation(stored.data):
            if stored.has_error:
                raise CommandError(f'page={page.pk} locale={locale.language_code}: incomplete translation')
            continue
        if stored:
            bad_ids.append(stored.pk)
        pending[segment.string].append(segment.path)
    return pending, bad_ids


def target_is_current(page, locale, source, publish):
    target = page.get_translation_or_none(locale)
    if source is None or target is None or target.alias_of_id:
        return False
    if publish and (not target.live or target.has_unpublished_changes):
        return False
    if json.loads(source.content_json) != json.loads(page.to_json()):
        return False
    last_save = source.translation_logs.filter(locale=locale).order_by('-created_at').first()
    if last_save is None or last_save.created_at < source.last_updated_at:
        return False
    return not StringTranslation.objects.filter(
        locale=locale, context__object_id=page.translation_key,
        updated_at__gt=last_save.created_at,
    ).exists()


def store_translations(source, locale, pending, translated, translator):
    if not pending:
        return
    segments = {
        (segment.context.path, segment.string.as_value()): segment
        for segment in source.stringsegment_set.select_related('context', 'string')
    }
    for string, paths in pending.items():
        for path in paths:
            segment = segments[path, string]
            StringTranslation.objects.get_or_create(
                translation_of_id=segment.string_id, context_id=segment.context_id,
                locale=locale, defaults={
                    'data': translated[string].data,
                    'translation_type': StringTranslation.TRANSLATION_TYPE_MACHINE,
                    'tool_name': translator.display_name,
                },
            )


def save_without_newsletter(translation, publish):
    # save_target copies synchronized fields before creating its revision. Clear the
    # flag in this in-memory snapshot only; the stored source stays faithful.
    content = json.loads(translation.source.content_json)
    if 'notify_subscribers' in content:
        content['notify_subscribers'] = False
        translation.source.content_json = json.dumps(content)
    if publish:
        translation.save_target(publish=True)
        return
    save_draft(translation)


def save_draft(translation):
    target = Page.objects.filter(
        translation_key=translation.source.object_id, locale=translation.target_locale,
    ).specific().first()
    live_content = None
    if target and target.live and not target.alias_of_id:
        live_content = target.serializable_data()
        if 'notify_subscribers' in live_content:
            live_content['notify_subscribers'] = False
    if target and target.alias_of_id:
        target.live = False
        target.save(update_fields=['live'])
    translation.save_target(publish=False)
    if live_content is not None:
        # Localize 1.14 saves content to the page row even for draft saves. Restore
        # the published content while retaining the new revision and draft metadata.
        target.refresh_from_db()
        target.with_content_json(live_content).save(clean=False)


def translate_page(page, locale, translator, publish):
    pending, bad_ids = pending_strings(page, locale)
    characters = sum(len(string.data) for string in pending)
    # Deduplicate equal strings across contexts; call the API before taking a write lock.
    translated = translator.translate(page.locale, locale, pending.keys()) if pending else {}
    with transaction.atomic():
        source, _ = TranslationSource.update_or_create_from_instance(page)
        translation, _ = Translation.objects.get_or_create(source=source, target_locale=locale)
        if not translation.enabled:
            translation.enabled = True
            translation.save(update_fields=['enabled'])
        total, complete = translation.get_progress()
        if not pending and total == complete and target_is_current(page, locale, source, publish):
            return 0, 0, 'skipped'
        StringTranslation.objects.filter(pk__in=bad_ids).delete()
        store_translations(source, locale, pending, translated, translator)
        total, complete = translation.get_progress()
        if total != complete:
            raise CommandError(f'page={page.pk} locale={locale.language_code}: incomplete translation')
        save_without_newsletter(translation, publish)
    if page.is_site_root():
        # A translated site root can change its slug and url_path; every process must
        # forget the old root paths or its pages stop resolving to URLs.
        Site.clear_site_root_paths_cache()
    return len(pending), characters, 'published' if publish else 'draft'


# A model answer can be invalid for one page (bad JSON, a disallowed tag, a missing
# segment); skip that page and report it. Many in a row means the API itself is down.
MAX_FAILURES_IN_A_ROW = 3


def attempt_page(page, locale, translator, publish):
    try:
        return translate_page(page, locale, translator, publish)
    except (ValueError, RuntimeError) as error:
        print(f'page={page.pk} locale={locale.language_code} error: {error}', file=sys.stderr)
        return 0, 0, 'failed'


class Command(BaseCommand):
    help = 'Machine-translate live default-locale pages and publish them without newsletters.'

    def add_arguments(self, parser):
        parser.add_argument('--locale', action='append', help='Target locale code (repeatable).')
        parser.add_argument('--limit', type=int, help='Maximum source pages per locale.')
        parser.add_argument('--page', action='append', type=int, help='Source page ID (repeatable).')
        parser.add_argument('--dry-run', action='store_true', help='Show counts without writes or API calls.')
        parser.add_argument('--no-publish', action='store_true', help='Save translated revisions as drafts.')

    def handle(self, *args, **options):
        source_locale = Locale.get_default()
        locales = self.get_locales(source_locale, options['locale'])
        pages = self.get_pages(source_locale, options['page'], options['limit'])
        dry_run = options['dry_run']
        publish = not options['no_publish']
        translator = None if dry_run else get_machine_translator()
        if not dry_run and translator is None:
            raise CommandError('No machine translator configured.')
        totals = dict(pages=0, strings=0, characters=0, published=0, draft=0, skipped=0, failed=0)
        failures_in_a_row = 0
        for locale in locales:
            for page in pages:
                if dry_run:
                    count, characters, status = self.plan_page(page, locale, publish)
                else:
                    count, characters, status = attempt_page(page, locale, translator, publish)
                    failures_in_a_row = failures_in_a_row + 1 if status == 'failed' else 0
                    if failures_in_a_row >= MAX_FAILURES_IN_A_ROW:
                        raise CommandError(f'{failures_in_a_row} pages failed in a row; stopping.')
                totals['pages'] += 1
                totals['strings'] += count
                totals['characters'] += characters
                totals[status] += 1
                prefix = 'would-' if dry_run and status != 'skipped' else ''
                self.stdout.write(
                    f'page={page.pk} locale={locale.language_code} strings={count} '
                    f'characters={characters} {prefix}{status}'
                )
        label = 'Dry-run totals' if dry_run else 'Totals'
        self.stdout.write(label + ': ' + ' '.join(f'{key}={value}' for key, value in totals.items()))

    def get_locales(self, source_locale, codes):
        locales = Locale.objects.exclude(pk=source_locale.pk).order_by('language_code')
        if codes:
            locales = locales.filter(language_code__in=codes)
            if set(codes) != set(locales.values_list('language_code', flat=True)):
                raise CommandError('Every --locale must name an existing non-source locale.')
        return list(locales)

    def get_pages(self, source_locale, ids, limit):
        if limit is not None and limit < 1:
            raise CommandError('--limit must be positive.')
        pages = Page.objects.live().filter(locale=source_locale, depth__gt=1).order_by('path')
        if ids:
            pages = pages.filter(pk__in=ids)
            if set(ids) != set(pages.values_list('pk', flat=True)):
                raise CommandError('Every --page must name a live source page below the tree root.')
        return list(pages[:limit].specific())

    def plan_page(self, page, locale, publish):
        pending, _ = pending_strings(page, locale)
        source = TranslationSource.objects.filter(object_id=page.translation_key, locale=page.locale).first()
        status = 'published' if publish else 'draft'
        if not pending and target_is_current(page, locale, source, publish):
            status = 'skipped'
        return len(pending), sum(len(string.data) for string in pending), status

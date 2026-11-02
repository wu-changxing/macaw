// Sign-to-comment: ask the wallet to sign the comment text, then POST it with the signature.
// The message format comes from the server (data-message) so both sides always build the same string.
(function () {
  const root = document.getElementById("wallet-comments");
  if (!root) return;
  const form = root.querySelector("[data-comment-form]");
  const status = root.querySelector("[data-status]");
  const list = root.querySelector("[data-comment-list]");

  if (!window.ethereum) return;
  form.hidden = false;
  root.querySelector("[data-wallet-help]").hidden = true;

  const toHex = (text) =>
    "0x" + Array.from(new TextEncoder().encode(text), (b) => b.toString(16).padStart(2, "0")).join("");

  function render(comment) {
    root.querySelector("[data-empty]")?.remove();
    const li = document.createElement("li");
    li.className = "bg-white rounded p-4 shadow-sm";
    const meta = document.createElement("div");
    meta.className = "text-sm text-gray-600 mb-1";
    meta.textContent = comment.address + " · " + root.dataset.justNow;
    const body = document.createElement("p");
    body.className = "text-gray-800 whitespace-pre-line break-words";
    body.textContent = comment.body;
    li.append(meta, body);
    list.append(li);
    const count = root.querySelector("[data-comment-count]");
    count.textContent = Number(count.textContent) + 1;
  }

  async function submit(body) {
    const [address] = await window.ethereum.request({ method: "eth_requestAccounts" });
    const issuedAt = new Date().toISOString();
    const message = root.dataset.message
      .replace("{page_id}", () => root.dataset.pageId)
      .replace("{issued_at}", () => issuedAt)
      .replace("{body}", () => body);
    status.textContent = root.dataset.confirm;
    const signature = await window.ethereum.request({ method: "personal_sign", params: [toHex(message), address] });
    const response = await fetch(root.dataset.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": form.csrfmiddlewaretoken.value },
      body: JSON.stringify({ page_id: Number(root.dataset.pageId), body, issued_at: issuedAt, address, signature }),
    });
    const result = await response.json().catch(() => ({ error: root.dataset.serverError }));
    if (!response.ok) throw new Error(result.error);
    return result;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    try {
      render(await submit(form.body.value.trim()));
      form.reset();
      status.textContent = root.dataset.posted;
    } catch (err) {
      // Wallet rejection (code 4001), network failure or a server-side refusal: say why, keep the form usable.
      status.textContent = err.code === 4001 ? root.dataset.cancelled : err.message || root.dataset.failed;
    } finally {
      button.disabled = false;
    }
  });
})();

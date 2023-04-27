
import React from 'react';

function Authors({ authors }) {
  return (
    <div className="mt-2 text-right text-sm text-neutral-500">
      <span className="text-gray-400">@</span>
      {authors.map((item) => (
        <a
          key={item.id}
          href={item.meta.html_url} // Update the href to use item.meta.html_url
          className="text-center underline underline-offset-1 decoration-gray-300 decoration-1 hover:ease-in-out hover:decoration-basicBlue"
        >
          {item.title} // Update to use item.title
        </a>
      ))}
    </div>
  );
}

export default Authors;

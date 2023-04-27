
import React from 'react';

function Title({ title }) {
  return (
    <h2 className="text-3xl font-bold text-center text-neutral-500 underline underline-offset-8 decoration-gray-300 decoration-1 hover:decoration-basicBlue overflow-clip">
      {title}
    </h2>
  );
}

export default Title;

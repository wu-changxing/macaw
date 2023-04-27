
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';

function FlexPageList() {
  const [pages, setPages] = useState([]);

  useEffect(() => {
    const fetchPages = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/v2/pages/?type=flex.Engineer&fields=*');
        setPages(response.data.items);
      } catch (error) {
        console.error('Error fetching pages:', error);
      }
    };

    fetchPages();
  }, []);

  return (
    <div className="container mx-auto px-4">
      <h1 className="text-4xl font-bold mb-4">Flex Pages</h1>
      <ul className="space-y-4">
        {pages.map((page) => (
          <li key={page.id} className="border border-gray-300 p-4 rounded">
            <Link to={`/engineer/${page.meta.slug}`} className="text-lg font-medium hover:text-blue-600">
              {page.title}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default FlexPageList;

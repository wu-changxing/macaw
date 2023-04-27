
import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const FlexPage = () => {
  const [pageData, setPageData] = useState(null);
  const { slug } = useParams();

const renderContentBlock = (block) => {
  switch (block.type) {
    case 'full_richtext':
    case 'simple_richtext':
      return <div dangerouslySetInnerHTML={{ __html: block.value }}></div>;
    case 'math':
      return <div>{block.value}</div>;
    case 'codeblock':
      return (
        <pre>
          <code>{block.value[0].code}</code>
        </pre>
      );
    // Add more cases for other block types if needed
    default:
      return null;
  }
};
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/v2/pages/?type=flex.Engineer&fields=content,title,slug,date,engineers&slug=${slug}`);
        setPageData(response.data.items[0]);
        console.log(response.data.items[0]);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, [slug]);

  if (!pageData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="bg-white">
      <div className="mx-auto py-12 px-4 max-w-7xl sm:px-6 lg:px-8">
        <div className="lg:text-center">
          <h2 className="text-base text-indigo-600 font-semibold tracking-wide uppercase">{pageData.title}</h2>
          <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 sm:text-4xl">{pageData.date}</p>
        </div>

        <div className="mt-10">
          <div className="mt-8 space-y-6">
            {pageData.engineers.map((engineer, index) => (
              <div key={index} className="text-lg leading-6 font-medium space-y-1">
                <h3 className="text-lg leading-6 font-medium text-gray-900">{engineer.author_name}</h3>
              </div>
            ))}
          </div>

          <div className="prose prose-indigo mt-8 space-y-6">
              {pageData.content.map((block) => renderContentBlock(block))}
        </div>
        </div>

      </div>
    </div>
  );
};

export default FlexPage;

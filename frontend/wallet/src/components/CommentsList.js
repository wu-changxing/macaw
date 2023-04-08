import { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEdit, faTrash, faUser } from "@fortawesome/free-solid-svg-icons";

const CommentsList = (props) => {
    const [displayedComments, setDisplayedComments] = useState([]);
    useEffect(() => {
        setDisplayedComments(props.comments); }, [props.comments]);
    
    

    return (
        <>
            {displayedComments.map((comment) => (
                <article className="p-6 text-base bg-white border-t border-gray-200 dark:border-gray-700 dark:bg-gray-900">
                    <footer className="flex justify-between space-x-2 items-center mb-2">
                        <div className="flex items-center">
                            <p className="inline-flex items-center mr-3 text-sm text-gray-900 dark:text-white">
                                <img
                                    className="mr-2 w-6 h-6 rounded-full"
                                    src={comment.avatarUrl}
                                    alt="Helene Engels"
                                ></img>
                                {comment.name}
                            </p>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                <time pubdate datetime="2022-06-23" title="June 23rd, 2022">
                                    {" "}
                                    {comment.date}{" "}
                                </time>
                            </p>
                        </div>
                        {comment.address.toLowerCase() === props.currentUserId && (
                            <div className="flex justify-end items-center">
                                <button
                                    onClick={() => props.onEdit(comment.id)}
                                    className="p-2 text-gray-400 bg-white rounded-lg hover:bg-gray-100 focus:ring-4 focus:outline-none focus:ring-gray-50 dark:bg-gray-900 dark:hover:bg-gray-700 dark:focus:ring-gray-600"
                                    type="button"
                                >
                                    <FontAwesomeIcon icon={faEdit} />
                                </button>
                                <button
                                    onClick={() => props.onDelete(comment.id)}
                                    className="ml-2 p-2 text-gray-400 bg-white rounded-lg hover:bg-gray-100 focus:ring-4 focus:outline-none focus:ring-gray-50 dark:bg-gray-900 dark:hover:bg-gray-700 dark:focus:ring-gray-600"
                                    type="button"
                                >
                                    <FontAwesomeIcon icon={faTrash} />
                                </button>
                            </div>
                        )}
                    </footer>
                    <p className="text-gray-500 dark:text-gray-400">{comment.content}   </p>
                    <div className="flex items-center mt-4 space-x-4">
                        <button
                            type="button"
                            className="flex items-center text-sm text-gray-500 hover:underline dark:text-gray-400"
                        >
                            <svg
                                aria-hidden="true"
                                className="mr-1 w-4 h-4"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.5829 8z"
                                ></path>
                            </svg>
                            Reply
                        </button>
                    </div>
                </article>
            ))}
        </>
    );
};

export default CommentsList;

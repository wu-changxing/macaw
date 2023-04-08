// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract CommentStorage {
    address public owner;
    struct Comment {
        address user;
        string content;
    }

    Comment[] public comments;
    mapping(address => string) public userNames;

    event CommentAdded(address indexed user, string content);
    event CommentUpdated(uint256 indexed commentId, string newContent);
    event CommentDeleted(uint256 indexed commentId);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the contract owner can call this function.");
        _;
    }

    modifier onlyCommentAuthorOrOwner(uint256 commentId) {
        require(
            msg.sender == comments[commentId].user || msg.sender == owner,
            "Only the comment author or contract owner can call this function."
        );
        _;
    }

    function addComment(string memory content) public {
        comments.push(Comment(msg.sender, content));
        emit CommentAdded(msg.sender, content);
    }

    function updateComment(uint256 commentId, string memory newContent)
        public
        onlyCommentAuthorOrOwner(commentId)
    {
        comments[commentId].content = newContent;
        emit CommentUpdated(commentId, newContent);
    }

    function deleteComment(uint256 commentId) public onlyCommentAuthorOrOwner(commentId) {
        comments[commentId] = comments[comments.length - 1];
        comments.pop();
        emit CommentDeleted(commentId);
    }

    function getCommentsCount() public view returns (uint256) {
        return comments.length;
    }

    function setUserName(string memory name) public {
        userNames[msg.sender] = name;
    }

    function editUserName(string memory newName) public {
        require(bytes(userNames[msg.sender]).length > 0, "User name not found.");
        userNames[msg.sender] = newName;
    }
}

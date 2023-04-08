import React from 'react';
import ProfilePopup from './ProfilePopup';
import contractABI from './contractABI.json';

import { useState, useEffect, useContext, useRef } from "react";
import { ethers } from "ethers";
import { AddressContext, NameContext } from './Auth';
import { Contract } from "@ethersproject/contracts";
import { Web3Provider } from "@ethersproject/providers";

import CommentsList from "./CommentsList";
const contractAddress = "0x27eEBcEb82B1c94d18e5BAe31c4c03896A939395";

function formatDate(date) {
  return date.toLocaleDateString();
}


function Comments() {
  const {name, setName} = useContext(NameContext)
  const {account, setAccount}= useContext(AddressContext)
  const [accountAddress, setAccountAddress] = useState(localStorage.getItem("address"));
  const [accountName, setAccountName] = useState(localStorage.getItem("name"));
  const [provider, setProvider] = useState(); // Add this line to manage provider state
  const [signer, setSigner] = useState();
  const [contract, setContract] = useState();
  const isLoggedIn = account !== "undefined"; // Check if the user is logged in
  const [content, setContent] = useState("");
  const [comment, setComment] = useState(
    {
      name: name,
      address: account,
      avatarUrl: "https://eu.ui-avatars.com/api/?name=John+Doe&size=250",
      date: formatDate(new Date()),
      content: content,
    }
  );
  const [comments, setComments] = useState([]);
  const [showProfilePopup, setShowProfilePopup] = useState(false);
  const loadComments = async () => {
    if (typeof window.ethereum !== "undefined") {
      try {
        const provider = new Web3Provider(window.ethereum);
        setProvider(provider); // Add this line to set the provider
        const signer = provider.getSigner();
        setSigner(signer);
        const contract = new Contract(contractAddress, contractABI, provider);

        const count = await contract.getCommentsCount();

        const newComments = [];
        for (let i = 0; i < count; i++) {
          const commentData = await contract.comments(i);
          newComments.push({
            name: commentData.user, // Update this according to your desired format
            address: commentData.user,
            date: formatDate(new Date()),
            avatarUrl: `https://eu.ui-avatars.com/api/?name=${commentData.user}&size=250`,
            content: commentData.content,
          });
        }

        setComments(newComments);
      } catch (err) {
        console.error("Error while loading comments:", err);
      }
    } else {
      console.error("Ethereum provider not detected");
    }
  };

  const onClickHandler = async () => {
    if (!isLoggedIn) {
      alert("Please log in to submit a comment.");
      console.log("Please log in to submit a comment.");
      return;
    }
    if (typeof window.ethereum !== "undefined") {
      try {
        const provider = new Web3Provider(window.ethereum);
        const signer = provider.getSigner();

        setContract(new Contract(contractAddress, contractABI, signer));


        // Send a transaction to add the comment
        const tx = await contract.addComment(comment.content);
        await tx.wait();

        // Reload the comments from the smart contract
        loadComments();
      } catch (err) {
        console.error("Error while adding the comment:", err);
      }
    } else {
      console.error("Ethereum provider not detected");
      alert("Ethereum provider not detected, please install MetaMask.")
    }
  };


  const onChangeHandler = (e) => {

    setComment({
      name: name,
      address: account,
      date: formatDate(new Date()),
      avatarUrl: "https://eu.ui-avatars.com/api/?name=" + name + "&size=250",
      content: e.target.value,
    });
  };
  useEffect(() => {
    loadComments();
    console.log(name);
    console.log(account);

  }, []);


  const handleEdit = async (commentId, newContent) => {
    if (typeof window.ethereum !== "undefined") {
      try {
        const provider = new Web3Provider(window.ethereum);


        const tx = await contract.updateComment(commentId, newContent);
        await tx.wait();

        loadComments();
      } catch (err) {
        console.error("Error while updating the comment:", err);
      }
    } else {
      console.error("Ethereum provider not detected");
    }
  };

  const handleDelete = async (commentId) => {
    if (typeof window.ethereum !== "undefined") {
      try {
        const provider = new Web3Provider(window.ethereum);
        const signer = provider.getSigner();
        const contract = new Contract(contractAddress, contractABI, signer);

        const tx = await contract.deleteComment(commentId);
        await tx.wait();

        loadComments();
      } catch (err) {
        console.error("Error while deleting the comment:", err);
      }
    } else {
      console.error("Ethereum provider not detected");
    }
  };
  const fd = {
    date: new Date(),
    text: 'I hope you enjoy learning React!',
    author: {
      name: 'Hello Kitty',
      avatarUrl: "https://robohash.org/30bf24022ceba039d24a419efa270be9?set=set4&bgset=&size=400x400"
    }
  };


  return (


    <div className="max-w-2xl font-thin mx-auto p-20 mt-20 shadow-xl">
      <ProfilePopup
        show={showProfilePopup}
        onSubmit={() => {
          setShowProfilePopup(false);
        }}
        onCancel={() => setShowProfilePopup(false)}
        signer={signer}
        contract={contract}
        contractAddress={contractAddress}
        contractABI={contractABI}
      />
      <CommentsList comments={comments}
        onEdit={handleEdit}
        onDelete={handleDelete}
        currentUserId={account}
      />

      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg lg:text-2xl font-bold text-gray-900 dark:text-white">Discussion </h2>
      </div>

      <div class="mb-6">
        <div class="py-2 px-4 mb-4 bg-white rounded-lg rounded-t-lg border border-gray-200 dark:bg-gray-800 dark:border-gray-700">
          <label for="comment" class="sr-only">Your comment</label>


          <textarea id="comment-content" rows="6"
            onChange={onChangeHandler}
            class="px-0 w-full text-sm text-gray-900 border-0 focus:ring-0 focus:outline-none dark:text-white dark:placeholder-gray-400 dark:bg-gray-800"
            placeholder="Write a comment..." required></textarea>
        </div>
        <div class="flex flex-row my-10">
          <img class="w-12 h-12 border-2 border-gray-300 rounded-full" alt="Anonymous's avatar"
            src="https://robohash.org/30bf24022ceba039d24a419efa270be9?set=set4&bgset=&size=400x400">
          </img>

          <div class="flex flex-col mt-1">
            <div class="flex items-center flex-1 px-4 font-bold leading-tight">
              {accountName}
              <button
                class="ml-2 text-xs text-gray-500 hover:text-blue-500 focus:outline-none"
                onClick={() => setShowProfilePopup(true)}
              >
                Edit
              </button>
            </div>
            <span class="px-4 text-xs font-normal text-gray-500">
              post use this address {accountAddress}
            </span>
          </div>


        </div>
        <button
          onClick={onClickHandler}
          class="w-full bg-sky-500 items-center py-2.5 px-4 mr-10 text-xl text-center text-white">
          Submit
        </button>
        {!isLoggedIn && (
          <p class="text-center text-red-500 mt-2">
            Please log in to submit a comment.
          </p>
        )}
      </div>
    </div>
  );
}

export default Comments;

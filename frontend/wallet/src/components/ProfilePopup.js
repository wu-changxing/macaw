
import React, { useState , useContext} from 'react';
import { name, setName } from "./WalletCardEthers";
import { ethers } from 'ethers';

import { AddressContext, NameContext } from "./Auth";
const ProfilePopup = ({ show, onSubmit, onCancel, signer, contract, contractAddress, contractABI }) => {
    const [newName, setNewName] = useState("");

    const { name, setName } = useContext(NameContext);
    const handleSubmit = async () => {
        console.log("Submitting new name:", newName)
        if (!newName) return;

        // Interact with your smart contract to update the name
        const contractInstance = new ethers.Contract(contractAddress, contractABI, signer);
        const updateNameTx = await contractInstance.setUserName(newName);
        onCancel();
        setName(newName);

        localStorage.setItem("name", newName);
        console.log("Waiting for transaction to be mined...");
        await updateNameTx.wait();
        console.log("Transaction mined! new name:", newName);
        Window.sessionStorage.setItem("name", newName);


        onSubmit();
    };

    if (!show) {
        return null;
    }

    return (
        <div className="fixed inset-0 flex items-center justify-center z-50">
            <div className="absolute inset-0 bg-black opacity-40 z-10"></div>
            <div className="p-6 bg-white rounded-md shadow-xl z-20">
                <h2 className="mb-4 text-xl font-bold">Edit Name</h2>
                <input
                    type="text"
                    className="w-full p-2 mb-4 text-gray-900 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white dark:bg-gray-800 dark:border-gray-700 dark:focus:bg-gray-700"
                    placeholder="Enter your name"
                    value={newName} // Change name to newName
                    onChange={(e) => setNewName(e.target.value)} // Change setName to setNewName
                />
                <div className="flex justify-end">
                    <button
                        className="px-4 py-2 font-semibold text-gray-700 bg-white border border-gray-300 rounded-md shadow-md hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onClick={onCancel}
                    >
                        Cancel
                    </button>
                    <button
                        className="px-4 py-2 ml-2 font-semibold text-white bg-blue-500 rounded-md shadow-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onClick={handleSubmit}
                    >
                        Save
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProfilePopup;


import React, { createContext, useState } from 'react';

const AddressContext = createContext("");
const NameContext = createContext("");

export const AccountProvider = ({ children }) => {
  // create the context state and update function
  const [address, setAddress] = useState("");
  const [name, setName] = useState("");

  return (
    <AddressContext.Provider value={{ address, setAddress }}>
      <NameContext.Provider value={{ name, setName }}>
        {children}
      </NameContext.Provider>
    </AddressContext.Provider>
  );
};

export { AddressContext, NameContext };

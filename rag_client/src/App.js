import React, { useState } from "react";
import SideBar from "./components/SideBar";
import TextInput from "./components/TextInput";
import FileInput from "./components/FileInput";
import ChatArea from "./components/ChatArea";
import { Box } from "@mui/material";

const App = () => {
  const [chatHistory, setChatHistory] = useState([
    { title: "最初のチャット" },
  ]);
  const [messages, setMessages] = useState([]);

  const handleSendMessage = (text) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "question", content: text },
    ]);
    // 仮のチャットの回答
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "answer", content: "これはチャットからの仮の回答です。" },
    ]);
  };

  const handleFileUpload = (fileName) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { type: "file", content: fileName },
    ]);
  };

  const handleSelectChat = (chat) => {
    console.log("Selected chat:", chat);
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* サイドバー */}
      <SideBar chatHistory={chatHistory} onSelectChat={handleSelectChat} />

      {/* メインチャットエリア */}
      <Box sx={{ flexGrow: 1, display: "flex", flexDirection: "column" }}>
        <Box sx={{ flexGrow: 1, overflowY: "auto", padding: 2 }}>
          <ChatArea messages={messages} />
        </Box>

        {/* メッセージ入力エリア */}
        <Box sx={{ padding: 2, borderTop: "1px solid #ddd", display: "flex", justifyContent: "center" }}>
          <FileInput onFileUpload={handleFileUpload} />
          <TextInput onSendMessage={handleSendMessage} />
        </Box>
      </Box>
    </Box>
  );
};

export default App;

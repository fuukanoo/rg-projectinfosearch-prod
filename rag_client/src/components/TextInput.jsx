import React, { useState } from "react";
import { Box, TextField, IconButton } from "@mui/material";
import SendIcon from "@mui/icons-material/Send";

const TextInput = ({ onSendMessage }) => {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (text.trim()) {
      onSendMessage(text);
      setText("");
    }
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center", padding: "8px", width: "60%" }}>
      <TextField
        fullWidth
        variant="outlined"
        placeholder="質問を入力してください..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        sx={{ marginRight: "8px", flexGrow: 1 }} // flexGrow で幅を自動調整
      />
      <IconButton color="primary" onClick={handleSend}>
        <SendIcon />
      </IconButton>
    </Box>
  );
};

export default TextInput;

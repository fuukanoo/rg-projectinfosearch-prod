import React, { useState } from "react";
import { Box, TextField, Button } from "@mui/material";

const TextInput = ({ onSendMessage }) => {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (text.trim()) {
      onSendMessage(text); // テキストを親に渡す
      setText(""); // 入力フィールドをクリア
    }
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center", width: "70%" }}>
      <TextField
        fullWidth
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="メッセージを入力..."
        variant="outlined"
        size="small"
      />
      <Button onClick={handleSend} variant="contained" sx={{ marginLeft: 2 }}>
        送信
      </Button>
    </Box>
  );
};

export default TextInput;

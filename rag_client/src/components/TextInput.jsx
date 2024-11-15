import React, { useState } from "react";
import { TextField, Typography, Box } from "@mui/material";

const TextInputWithMaterialUI = () => {
  const [text, setText] = useState("");

  // テキスト変更時のイベントハンドラー
  const handleChange = (event) => {
    setText(event.target.value);
  };

  return (
    <Box sx={{ padding: "20px", maxWidth: "400px", margin: "0 auto" }}>
      <Typography variant="h5" gutterBottom>
        Material-UI Text Input Component
      </Typography>
      <TextField
        label="Type something..."
        variant="outlined"
        fullWidth
        value={text}
        onChange={handleChange}
        sx={{ marginBottom: "20px" }}
      />
      <Typography variant="body1">
        You typed: <strong>{text}</strong>
      </Typography>
    </Box>
  );
};

export default TextInputWithMaterialUI;

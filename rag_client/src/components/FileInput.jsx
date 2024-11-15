import React, { useState } from "react";
import { Button, Typography, Box } from "@mui/material";

const FileUpload = () => {
  const [fileName, setFileName] = useState("");

  // ファイルが選択されたときのイベントハンドラー
  const handleFileChange = (event) => {
    if (event.target.files.length > 0) {
      setFileName(event.target.files[0].name);
    }
  };

  return (
    <Box sx={{ padding: "20px", maxWidth: "400px", margin: "0 auto", textAlign: "center" }}>
      <Button
        variant="contained"
        component="label"
        sx={{ marginBottom: "20px" }}
      >
        Upload File
        <input
          type="file"
          hidden
          onChange={handleFileChange}
        />
      </Button>
    </Box>
  );
};

export default FileUpload;

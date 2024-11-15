import React, { useState } from "react";
import { Box, Button } from "@mui/material";
import UploadFileIcon from '@mui/icons-material/UploadFile';
import axios from "axios";

const FileInput = ({ onFileUpload }) => {
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (event) => {
    if (event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await axios.post("http://localhost:7071/api/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      onFileUpload(selectedFile.name);  // ファイル名をChatAreaに表示
      setSelectedFile(null);
    } catch (error) {
      console.error("Error uploading file:", error);
    }
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center" }}>
      <Button
        variant="outlined"
        component="label"
        startIcon={<UploadFileIcon />}
      >
        ファイルを選択
        <input
          type="file"
          hidden
          onChange={handleFileChange}
        />
      </Button>
      <Button
        variant="contained"
        color="primary"
        onClick={handleFileUpload}
        disabled={!selectedFile}
        sx={{ marginLeft: "8px" }}
      >
        ファイルを送信
      </Button>
    </Box>
  );
};

export default FileInput;

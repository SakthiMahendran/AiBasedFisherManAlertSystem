import React from "react";
import { Box } from "@mui/material";

const CenteredContainer = ({ children }) => {
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="#f5f5f5"
      padding="1rem"
    >
      <Box
        sx={{
          width: "100%",
          maxWidth: "400px",
          backgroundColor: "white",
          padding: "2rem",
          borderRadius: "12px",
          boxShadow: 3,
        }}
      >
        {children}
      </Box>
    </Box>
  );
};

export default CenteredContainer;

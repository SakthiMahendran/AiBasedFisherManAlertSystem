import React, { useContext, useState } from "react";
import {
  Box,
  TextField,
  Button,
  Typography,
  Paper,
  Alert,
  Link as MuiLink,
  InputAdornment,
  IconButton,
  CircularProgress,
} from "@mui/material";
import { Visibility, VisibilityOff } from "@mui/icons-material";
import { Link, useNavigate } from "react-router-dom";
import axiosInstance from "../utils/axiosInstance";
import { AuthContext } from "./AuthProvider";

const LoginPage = () => {
  const { login } = useContext(AuthContext); // Use AuthContext for global authentication state
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [error, setError] = useState(null); // Error message state
  const [showPassword, setShowPassword] = useState(false); // Password visibility toggle
  const [isLoading, setIsLoading] = useState(false); // Loading state for button

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials((prev) => ({ ...prev, [name]: value }));

    // Clear error on user input
    setError(null);
  };

  const handleLogin = async () => {
    if (!credentials.username || !credentials.password) {
      setError("Both username and password are required.");
      return;
    }

    setIsLoading(true); // Start loading
    try {
      const response = await axiosInstance.post("/api/auth/login/", credentials);

      // On success, update authentication state and navigate to home
      login(response.data); // Save token or user info in AuthContext
      navigate("/home"); // Redirect to the home page
    } catch (err) {
      const backendError = err.response?.data?.error || "Login failed. Please try again.";
      setError(backendError);
    } finally {
      setIsLoading(false); // Stop loading
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword((prev) => !prev);
  };

  const isDisabled = !credentials.username || !credentials.password || isLoading; // Disable button if fields are empty or loading

  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="100vh"
      bgcolor="#f5f5f5"
      padding="1rem"
    >
      <Paper
        elevation={3}
        sx={{
          padding: "2rem",
          width: "100%",
          maxWidth: "400px",
          borderRadius: "12px",
          textAlign: "center",
          backgroundColor: "white",
        }}
      >
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Welcome Back!
        </Typography>
        <Typography variant="body1" color="textSecondary" marginBottom="1.5rem">
          Please login to continue
        </Typography>

        {error && (
          <Alert
            severity="error"
            sx={{ marginBottom: "1rem" }}
            onClose={() => setError(null)}
          >
            {error}
          </Alert>
        )}

        <TextField
          label="Username"
          name="username"
          value={credentials.username}
          onChange={handleInputChange}
          fullWidth
          margin="normal"
          disabled={isLoading}
        />
        <TextField
          label="Password"
          name="password"
          type={showPassword ? "text" : "password"}
          value={credentials.password}
          onChange={handleInputChange}
          fullWidth
          margin="normal"
          disabled={isLoading}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={togglePasswordVisibility} edge="end">
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
        <Button
          variant="contained"
          color="primary"
          fullWidth
          onClick={handleLogin}
          disabled={isDisabled}
          sx={{
            marginTop: "1.5rem",
            height: "48px",
            fontSize: "1rem",
          }}
        >
          {isLoading ? <CircularProgress size={24} color="inherit" /> : "Login"}
        </Button>

        <Typography variant="body2" marginTop="1.5rem">
          Don't have an account?{" "}
          <MuiLink
            component={Link}
            to="/signup"
            color="primary"
            underline="hover"
            sx={{ fontWeight: "bold" }}
          >
            Sign Up
          </MuiLink>
        </Typography>
      </Paper>
    </Box>
  );
};

export default LoginPage;

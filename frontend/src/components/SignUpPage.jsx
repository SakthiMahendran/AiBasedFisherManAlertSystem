import React, { useState } from "react";
import {
  Box,
  TextField,
  Button,
  Typography,
  InputAdornment,
  IconButton,
  Alert,
  CircularProgress,
  LinearProgress,
} from "@mui/material";
import { Link } from "react-router-dom";
import { Eye, EyeOff, Check, X } from "lucide-react";
import axiosInstance from "../utils/axiosInstance";
import CenteredContainer from "./CenteredContainer";

const SignUpPage = () => {
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState("");

  const validateEmail = (email) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const validatePassword = (password) => ({
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
  });

  const getPasswordStrength = (password) => {
    const checks = validatePassword(password);
    const strength = Object.values(checks).filter(Boolean).length;
    return (strength / 5) * 100;
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: "" })); // Clear field-specific errors
  };

  const handleSignUp = async () => {
    setErrors({});
    setSuccessMessage("");

    const newErrors = {};
    if (!validateEmail(formData.email)) newErrors.email = "Please enter a valid email address.";
    const passwordChecks = validatePassword(formData.password);
    if (!Object.values(passwordChecks).every(Boolean))
      newErrors.password = "Password doesn't meet all requirements.";
    if (formData.password !== formData.confirmPassword)
      newErrors.confirmPassword = "Passwords do not match.";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    try {
      const response = await axiosInstance.post("/api/auth/signup/", {
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });
      setSuccessMessage(response.data.message || "Account created successfully!");
      setFormData({ username: "", email: "", password: "", confirmPassword: "" });
    } catch (error) {
      const backendErrors = error.response?.data || {};
      setErrors({
        email: backendErrors.email || "",
        username: backendErrors.username || "",
        password: backendErrors.password || "",
        submit: backendErrors.message || "Failed to create account. Please try again.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const passwordStrength = getPasswordStrength(formData.password);

  return (
    <CenteredContainer>
      <Typography variant="h4" gutterBottom align="center" sx={{ mb: 3 }}>
        Create Account
      </Typography>

      {successMessage && (
        <Alert
          severity="success"
          sx={{ mb: 2 }}
          onClose={() => setSuccessMessage("")}
        >
          {successMessage}
        </Alert>
      )}

      {errors.submit && (
        <Alert
          severity="error"
          sx={{ mb: 2 }}
          onClose={() => setErrors((prev) => ({ ...prev, submit: "" }))}
        >
          {errors.submit}
        </Alert>
      )}

      <TextField
        label="Username"
        name="username"
        value={formData.username}
        onChange={handleInputChange}
        fullWidth
        margin="normal"
        error={!!errors.username}
        helperText={errors.username}
        disabled={isLoading}
      />

      <TextField
        label="Email"
        name="email"
        value={formData.email}
        onChange={handleInputChange}
        fullWidth
        margin="normal"
        error={!!errors.email}
        helperText={errors.email}
        disabled={isLoading}
      />

      <TextField
        label="Password"
        name="password"
        type={showPassword ? "text" : "password"}
        value={formData.password}
        onChange={handleInputChange}
        fullWidth
        margin="normal"
        error={!!errors.password}
        helperText={errors.password}
        disabled={isLoading}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton onClick={() => setShowPassword(!showPassword)}>
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      {formData.password && (
        <Box sx={{ mb: 2 }}>
          <LinearProgress
            variant="determinate"
            value={passwordStrength}
            sx={{
              mb: 1,
              height: 8,
              borderRadius: 1,
              backgroundColor: "grey.200",
              "& .MuiLinearProgress-bar": {
                backgroundColor:
                  passwordStrength <= 40
                    ? "error.main"
                    : passwordStrength <= 80
                    ? "warning.main"
                    : "success.main",
              },
            }}
          />
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
            {Object.entries(validatePassword(formData.password)).map(([key, valid]) => (
              <Box key={key} sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                {valid ? <Check size={16} color="green" /> : <X size={16} color="red" />}
                <Typography
                  variant="caption"
                  color={valid ? "success.main" : "error.main"}
                >
                  {key.charAt(0).toUpperCase() + key.slice(1)}
                </Typography>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      <TextField
        label="Confirm Password"
        name="confirmPassword"
        type={showConfirmPassword ? "text" : "password"}
        value={formData.confirmPassword}
        onChange={handleInputChange}
        fullWidth
        margin="normal"
        error={!!errors.confirmPassword}
        helperText={errors.confirmPassword}
        disabled={isLoading}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </IconButton>
            </InputAdornment>
          ),
        }}
      />

      <Button
        variant="contained"
        color="primary"
        fullWidth
        onClick={handleSignUp}
        disabled={isLoading}
        sx={{
          mt: 3,
          mb: 2,
          height: 48,
        }}
      >
        {isLoading ? <CircularProgress size={24} color="inherit" /> : "Create Account"}
      </Button>

      <Typography variant="body2" align="center">
        Already have an account?{" "}
        <Link to="/" style={{ color: "#1976d2", textDecoration: "none" }}>
          Login
        </Link>
      </Typography>
    </CenteredContainer>
  );
};

export default SignUpPage;

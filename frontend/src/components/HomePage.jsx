import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Alert,
  Paper,
  styled,
  Container,
  Stack,
  Grid,
  CircularProgress,
} from "@mui/material";
import axios from "axios";

const BASE_URL = "http://localhost:8000";

const FeatureCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  textAlign: "center",
  height: "100%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  gap: theme.spacing(2),
  backgroundColor: theme.palette.background.paper,
  transition: "transform 0.3s ease-in-out",
  "&:hover": {
    transform: "translateY(-5px)",
  },
}));

const BackgroundAnimation = styled("div")({
  position: "absolute",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  zIndex: -1,
  background: `linear-gradient(120deg, rgba(240, 248, 255, 0.5) 0%, rgba(224, 255, 255, 0.7) 50%, rgba(245, 245, 245, 0.5) 100%)`,
  backgroundSize: "400% 400%",
  animation: "gradient 10s ease infinite",
  "@keyframes gradient": {
    "0%": { backgroundPosition: "0% 50%" },
    "50%": { backgroundPosition: "100% 50%" },
    "100%": { backgroundPosition: "0% 50%" },
  },
});

const formatValue = (value, isDangerous) => {
  if (value < isDangerous.safe) {
    return <span style={{ color: "green" }}>{value} (Safe)</span>;
  } else if (value < isDangerous.avg) {
    return <span style={{ color: "orange" }}>{value} (Average Risk)</span>;
  } else {
    return <span style={{ color: "red" }}>{value} (Dangerous)</span>;
  }
};

const MapComponent = ({ onSelect }) => {
  useMapEvents({
    click: (e) => {
      const { lat, lng } = e.latlng;
      onSelect(lat, lng);
    },
  });
  return null;
};

const HomePage = () => {
  const [lat, setLat] = useState(null);
  const [lon, setLon] = useState(null);
  const [weatherData, setWeatherData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isLandSelected, setIsLandSelected] = useState(false);

  const handleFetchWeather = async () => {
    if (!lat || !lon) {
      setError("Please select a location in the ocean.");
      return;
    }

    setIsLoading(true);
    setWeatherData(null);
    setError(null);
    setIsLandSelected(false);

    try {
      const response = await axios.get(`${BASE_URL}/api/ai/weather/`, {
        params: { latitude: lat, longitude: lon },
      });
      setWeatherData(response.data.weather_data);
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message;

      if (errorMessage.includes("bad number 4294967382 for type uint32")) {
        setIsLandSelected(true);
        setError("You selected a land area where data cannot be fetched.");
      } else {
        setError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const markerIcon = new L.Icon({
    iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
  });

  return (
    <Box sx={{ minHeight: "100vh", position: "relative", overflow: "hidden" }}>
      <BackgroundAnimation />
      <Container maxWidth="lg" sx={{ pt: 8, pb: 8 }}>
        <Stack spacing={6}>
          <Box textAlign="center">
            <Typography
              variant="h2"
              component="h1"
              gutterBottom
              sx={{
                fontWeight: "bold",
                color: "#008080",
              }}
            >
              Ocean Weather Forecast by Ensemble Models
            </Typography>
            <Typography variant="h5" color="text.secondary" sx={{ mb: 4 }}>
              Select a location in the ocean to get weather forecasts.
            </Typography>
          </Box>

          <Box>
            <MapContainer
              center={[0, 0]}
              zoom={2}
              style={{ height: "400px", borderRadius: "8px", marginBottom: "16px" }}
            >
              <TileLayer
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
              />
              <MapComponent
                onSelect={(latitude, longitude) => {
                  setLat(latitude.toFixed(4));
                  setLon(longitude.toFixed(4));
                  setIsLandSelected(false); // Reset land selection flag
                  setError(null); // Clear previous errors
                }}
              />
              {lat && lon && <Marker position={[lat, lon]} icon={markerIcon} />}
            </MapContainer>
            <Box textAlign="center">
              {lat && lon && (
                <Typography variant="body1" sx={{ mb: 1 }}>
                  <strong>Selected Latitude:</strong> {lat}, <strong>Longitude:</strong> {lon}
                </Typography>
              )}
              <Button
                variant="contained"
                size="large"
                onClick={handleFetchWeather}
                sx={{ mt: 2 }}
                disabled={isLoading || isLandSelected}
              >
                {isLoading ? <CircularProgress size={24} color="inherit" /> : "Fetch Data"}
              </Button>
            </Box>
            {error && (
              <Alert severity={isLandSelected ? "warning" : "error"} sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>

          {weatherData && (
            <Box sx={{ mt: 6 }}>
              <Typography variant="h4" gutterBottom>
                Weather Insights
              </Typography>
              <Grid container spacing={3}>
                {Object.keys(weatherData).map((key) => (
                  <Grid item xs={12} sm={6} md={4} key={key}>
                    <FeatureCard>
                      <Typography variant="h6" gutterBottom>
                        {key.replace(/_/g, " ").toUpperCase()}
                      </Typography>
                      <Typography>
                        {formatValue(weatherData[key], {
                          safe: 2, // Customize thresholds
                          avg: 4,
                        })}
                      </Typography>
                    </FeatureCard>
                  </Grid>
                ))}
              </Grid>
            </Box>
          )}
        </Stack>
      </Container>
    </Box>
  );
};

export default HomePage;

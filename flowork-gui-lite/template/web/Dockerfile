#######################################################################
# WEBSITE https://flowork.cloud
# File NAME : C:\FLOWORK\flowork-gui\template\web\Dockerfile
# COMMENT: This Dockerfile is for building the GUI image.
# It's primarily used if you intend to self-host the GUI instead of
# using the version deployed on Cloudflare Pages.
# For the standard Open Core MVP setup, this file is not directly used
# during the `docker-compose up` process.
#######################################################################

# --- Stage 1: The Builder ---
# This stage installs Node.js, dependencies, and builds the Vue app.
FROM node:18-alpine as builder

# Set the working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application for production
RUN npm run build


# --- Stage 2: The Final Server (Nginx) ---
# This stage serves the built static files using a lightweight web server.
FROM nginx:1.25-alpine

# Copy the built files from the 'builder' stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the Nginx configuration file
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for Nginx
EXPOSE 80
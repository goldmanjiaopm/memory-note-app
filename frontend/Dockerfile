FROM node:19-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy app files
COPY . .

# Build the app
RUN npm run build

# Install serve to run the application
RUN npm install -g serve

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]

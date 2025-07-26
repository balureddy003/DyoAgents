FROM node:18-alpine

WORKDIR /app

COPY src/frontend/package*.json ./
RUN npm install

COPY src/frontend/ .
RUN npm run build

# Serve the static build using a lightweight server
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "5173"]
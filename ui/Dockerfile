# Local/compose image of the static UI. In Azure the same build output goes to Static Web Apps.
FROM node:24.22.3-alpine AS build
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci
COPY index.html tsconfig.json tsconfig.app.json tsconfig.node.json vite.config.ts ./
COPY public/ ./public/
COPY scripts/ ./scripts/
COPY src/ ./src/
ARG VITE_GAMES_API_URL=http://localhost:8001
ARG VITE_INSIGHTS_API_URL=http://localhost:8002
ENV VITE_GAMES_API_URL=$VITE_GAMES_API_URL \
    VITE_INSIGHTS_API_URL=$VITE_INSIGHTS_API_URL
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.31.7-alpine
COPY --from=build /src/dist/ /usr/share/nginx/html/
EXPOSE 8080

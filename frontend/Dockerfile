FROM node:22-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@11.19.0 --activate
COPY pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
COPY frontend/package.json ./frontend/
RUN pnpm config set --location=project storeDir /pnpm/store && pnpm config set --location=project cacheDir /pnpm/cache && pnpm config set --location=project stateDir /pnpm/state && pnpm install --frozen-lockfile
COPY frontend ./frontend
RUN cd frontend && pnpm build
FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
EXPOSE 80

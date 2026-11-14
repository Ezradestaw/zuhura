# Multi-Stage Hardened Production Build for Zuhura Frontend
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci || npm install

COPY . .
RUN npm run typecheck && npm run build

# Production Runtime Image
FROM node:20-alpine AS runner

WORKDIR /app
RUN npm install -g serve && \
    addgroup -g 1001 -S zuhura && \
    adduser -u 1001 -S zuhura -G zuhura

COPY --from=builder --chown=zuhura:zuhura /app/dist /app/dist

USER zuhura
EXPOSE 3000

ENV PORT=3000
CMD ["serve", "-s", "dist", "-l", "3000"]

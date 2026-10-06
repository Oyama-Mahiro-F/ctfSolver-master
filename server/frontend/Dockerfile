# 构建阶段：直接在前端源码上执行 npm build。
# 原实现依赖仓库中并不存在的 dist.zip，导致 docker build 必然失败。
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.25-alpine
WORKDIR /usr/share/nginx/html
RUN rm -rf /usr/share/nginx/html/*
COPY --from=builder /app/dist/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

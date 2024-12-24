# Stage 1
FROM node:lts-alpine AS builder

WORKDIR /app

COPY package.json yarn.lock ./

RUN yarn install --frozen-lockfile

COPY . .

RUN yarn build

# Stage 2
FROM node:lts-alpine

WORKDIR /app

RUN yarn global add serve

COPY --from=builder /app/dist ./dist

EXPOSE 8080

CMD [ "serve", "-s", "dist", "-l", "8080" ]

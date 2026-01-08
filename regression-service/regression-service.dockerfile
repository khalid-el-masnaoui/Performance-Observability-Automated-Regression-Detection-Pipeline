FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY app.js .

EXPOSE 8090

CMD ["node", "app.js"]

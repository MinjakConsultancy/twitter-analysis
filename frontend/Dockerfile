FROM node:12 as build

WORKDIR /usr/src/app

COPY ./package*.json ./

RUN npm install 

COPY . . 

#RUN npm run build --prod --configuration=production
RUN npm install @angular/cli -g
RUN ng build --prod
RUN rm -r src 

FROM nginx:latest

EXPOSE 8083

COPY --from=build /usr/src/app/dist/angular-app usr/share/nginx/html/
COPY ./nginx.conf /etc/nginx/nginx.conf

EXPOSE 8083

CMD ["nginx", "-g", "daemon off;"]
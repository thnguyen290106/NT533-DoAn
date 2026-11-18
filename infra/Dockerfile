FROM maven:3.9.9-eclipse-temurin-21 AS build
ARG SERVICE
WORKDIR /src
COPY services/${SERVICE}/pom.xml ./pom.xml
COPY services/${SERVICE}/src ./src
RUN mvn -B -ntp package -DskipTests

FROM eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /src/target/*-service-1.0.0.jar /app/service.jar
USER 10001:10001
ENTRYPOINT ["java", "-jar", "/app/service.jar"]

FROM maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS build
ARG SERVICE
WORKDIR /src
COPY services/${SERVICE}/pom.xml ./pom.xml
COPY services/${SERVICE}/src ./src
RUN mvn -B -ntp package -DskipTests

FROM eclipse-temurin:21-jre@sha256:ca73b4d3961703d6d7830a4361f49ef0478f8f28b39defc07bb72f4cc7f834f6
WORKDIR /app
COPY --from=build /src/target/*-service-1.0.0.jar /app/service.jar
USER 10001:10001
ENTRYPOINT ["java", "-jar", "/app/service.jar"]

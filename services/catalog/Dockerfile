FROM maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e AS build
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN mvn -B -ntp verify

FROM eclipse-temurin:21-jre@sha256:ca73b4d3961703d6d7830a4361f49ef0478f8f28b39defc07bb72f4cc7f834f6
WORKDIR /app
COPY --from=build /build/target/catalog-service-1.0.0.jar catalog.jar
USER 10001:10001
EXPOSE 8080 8082
ENTRYPOINT ["java", "-jar", "/app/catalog.jar"]

import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";

import Hero from "../components/Hero";
import Destinations from "../components/Destinations";
import PopularTours from "../components/PopularTours";
import About from "../components/About";
import Blog from "../components/Blog";

const Home = () => {
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const sectionId = params.get("scroll");
    if (sectionId) {
      const element = document.getElementById(sectionId);
      if (element) {
        // Chờ DOM render xong rồi scroll
        setTimeout(() => {
          element.scrollIntoView({ behavior: "smooth" });
        }, 100);
      }
    }
  }, [location]);

  return (
    <>
      <Hero />
      <Destinations />
      <PopularTours />
      <About />
      <Blog />
    </>
  );
};

export default Home;

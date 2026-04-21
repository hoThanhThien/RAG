import React, { useEffect, lazy, Suspense } from "react";
import { useLocation } from "react-router-dom";

import Hero from "../components/Hero";

const Destinations = lazy(() => import("../components/Destinations"));
const PopularTours = lazy(() => import("../components/PopularTours"));
const About = lazy(() => import("../components/About"));
const Blog = lazy(() => import("../components/Blog"));

export default function Home() {
  const location = useLocation();

  useEffect(() => {
    const id = new URLSearchParams(location.search).get("scroll");

    if (id) {
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({
          behavior: "smooth",
        });
      }, 100);
    }
  }, [location]);

  return (
    <>
      <Hero />

      <Suspense fallback={<div className="py-5 text-center">Loading...</div>}>
        <Destinations />
        <PopularTours />
        <About />
        <Blog />
      </Suspense>
    </>
  );
}
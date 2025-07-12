// import React from "react";
import dp from "@/assets/dp.png";

export function Footer() {
  return (
    <footer className="bg-muted mt-8">
      <div className="container mx-auto px-4 py-2 text-center text-sm text-muted-foreground">
       <img src={dp} alt="Logo" className="w-[40px] inline" />
        <p className="inline">&copy; 2025 DyoPods </p>
       

      </div>
    </footer>
  );
}

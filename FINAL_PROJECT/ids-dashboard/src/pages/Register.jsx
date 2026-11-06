import React from "react";
import { Link } from "react-router-dom";

export default function Register() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-gray-800 to-slate-900">
      <div className="bg-gray-800 p-8 rounded-2xl shadow-lg w-96">
        <h1 className="text-2xl font-bold text-center mb-6">📝 Create Account</h1>
        <form className="space-y-4">
          <input type="text" placeholder="Full Name" className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none" />
          <input type="email" placeholder="Email" className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none" />
          <input type="password" placeholder="Password" className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none" />
          <button type="submit" className="w-full bg-green-600 hover:bg-green-700 p-3 rounded-lg font-semibold">Register</button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-400">
          Already have an account?{" "}
          <Link to="/login" className="text-blue-400 hover:underline">Login</Link>
        </p>
      </div>
    </div>
  );
}

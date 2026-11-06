import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function Auth() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-gray-800 to-slate-900">
      <motion.div
        className="bg-gray-800/70 backdrop-blur-xl p-8 rounded-2xl shadow-2xl w-[90%] sm:w-96 border border-gray-700"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <h1 className="text-3xl font-bold text-center mb-6 text-white">
          {isLogin ? "🔐 Welcome Back" : "📝 Create an Account"}
        </h1>

        <AnimatePresence mode="wait">
          {isLogin ? (
            <motion.form
              key="login"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={{ duration: 0.3 }}
              className="space-y-4"
            >
              <input
                type="email"
                placeholder="Email"
                className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none"
              />
              <input
                type="password"
                placeholder="Password"
                className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none"
              />
              <button
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 p-3 rounded-lg font-semibold transition-all duration-200"
              >
                Login
              </button>
            </motion.form>
          ) : (
            <motion.form
              key="register"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={{ duration: 0.3 }}
              className="space-y-4"
            >
              <input
                type="text"
                placeholder="Full Name"
                className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none"
              />
              <input
                type="email"
                placeholder="Email"
                className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none"
              />
              <input
                type="password"
                placeholder="Password"
                className="w-full p-3 bg-gray-700 rounded-lg focus:outline-none"
              />
              <button
                type="submit"
                className="w-full bg-green-600 hover:bg-green-700 p-3 rounded-lg font-semibold transition-all duration-200"
              >
                Register
              </button>
            </motion.form>
          )}
        </AnimatePresence>

        <p className="text-center mt-6 text-gray-400 text-sm">
          {isLogin ? "Don’t have an account?" : "Already have an account?"}{" "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-400 hover:underline font-semibold"
          >
            {isLogin ? "Register here" : "Login here"}
          </button>
        </p>
      </motion.div>
    </div>
  );
}

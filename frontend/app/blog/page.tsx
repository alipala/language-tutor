'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Calendar, User, Clock, ArrowRight, BookOpen, Zap, Globe } from 'lucide-react';

const Blog: React.FC = () => {
  const featuredPost = {
    title: "The Science Behind AI-Powered Language Learning",
    excerpt: "Discover how our advanced AI algorithms adapt to your learning style and accelerate language acquisition through personalized conversations.",
    author: "Dr. Elena Petrov",
    date: "January 10, 2025",
    readTime: "8 min read",
    category: "Research",
    image: "/images/blog/featured.jpg"
  };

  const posts = [
    {
      title: "5 Tips for Effective Language Practice with AI",
      excerpt: "Maximize your learning potential with these proven strategies for AI conversation practice.",
      author: "Sarah Chen",
      date: "January 8, 2025",
      readTime: "5 min read",
      category: "Tips",
      icon: Zap
    },
    {
      title: "Breaking Language Barriers in Global Business",
      excerpt: "How multilingual communication skills are becoming essential in today's interconnected world.",
      author: "Marcus Rodriguez",
      date: "January 5, 2025", 
      readTime: "6 min read",
      category: "Business",
      icon: Globe
    },
    {
      title: "The Psychology of Language Learning Motivation",
      excerpt: "Understanding what drives successful language learners and how to maintain long-term motivation.",
      author: "Dr. Elena Petrov",
      date: "January 3, 2025",
      readTime: "7 min read",
      category: "Psychology",
      icon: BookOpen
    }
  ];

  const categories = ["All", "Research", "Tips", "Business", "Psychology", "Technology"];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-[#4ECFBF] to-[#3a9e92] text-white py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold mb-6">Language Learning Blog</h1>
            <p className="text-xl text-white/90 max-w-3xl mx-auto leading-relaxed">
              Insights, tips, and research from the world of AI-powered language learning. 
              Stay updated with the latest trends and best practices.
            </p>
          </motion.div>
        </div>
      </div>

      {/* Featured Post */}
      <div className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white rounded-2xl shadow-lg overflow-hidden border border-gray-200"
          >
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="bg-gradient-to-br from-[#4ECFBF]/20 to-[#3a9e92]/20 p-12 flex items-center justify-center">
                <BookOpen className="w-32 h-32 text-[#4ECFBF]" />
              </div>
              <div className="p-8 lg:p-12 flex flex-col justify-center">
                <div className="flex items-center mb-4">
                  <span className="px-3 py-1 bg-[#4ECFBF]/10 text-[#4ECFBF] rounded-full text-sm font-medium">
                    {featuredPost.category}
                  </span>
                  <span className="ml-2 text-gray-500 text-sm">Featured</span>
                </div>
                <h2 className="text-3xl font-bold text-gray-800 mb-4">{featuredPost.title}</h2>
                <p className="text-gray-600 leading-relaxed mb-6">{featuredPost.excerpt}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-gray-500 text-sm">
                    <User className="w-4 h-4 mr-2" />
                    <span className="mr-4">{featuredPost.author}</span>
                    <Calendar className="w-4 h-4 mr-2" />
                    <span className="mr-4">{featuredPost.date}</span>
                    <Clock className="w-4 h-4 mr-2" />
                    <span>{featuredPost.readTime}</span>
                  </div>
                  <button className="flex items-center text-[#4ECFBF] hover:text-[#3a9e92] font-medium">
                    Read More <ArrowRight className="w-4 h-4 ml-2" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Categories */}
      <div className="pb-8">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-wrap justify-center gap-4">
            {categories.map((category, index) => (
              <motion.button
                key={category}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * index }}
                className={`px-6 py-2 rounded-full font-medium transition-all duration-300 ${
                  category === "All" 
                    ? "bg-[#4ECFBF] text-white" 
                    : "bg-white text-gray-600 hover:bg-[#4ECFBF]/10 hover:text-[#4ECFBF] border border-gray-200"
                }`}
              >
                {category}
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      {/* Blog Posts */}
      <div className="pb-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {posts.map((post, index) => (
              <motion.div
                key={post.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="bg-white rounded-2xl shadow-lg border border-gray-200 overflow-hidden hover:shadow-xl transition-shadow duration-300"
              >
                <div className="bg-gradient-to-br from-[#4ECFBF]/20 to-[#3a9e92]/20 p-8 flex items-center justify-center">
                  <post.icon className="w-16 h-16 text-[#4ECFBF]" />
                </div>
                <div className="p-6">
                  <div className="flex items-center mb-3">
                    <span className="px-3 py-1 bg-[#4ECFBF]/10 text-[#4ECFBF] rounded-full text-sm font-medium">
                      {post.category}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-gray-800 mb-3">{post.title}</h3>
                  <p className="text-gray-600 leading-relaxed mb-4">{post.excerpt}</p>
                  <div className="flex items-center justify-between text-gray-500 text-sm">
                    <div className="flex items-center">
                      <User className="w-4 h-4 mr-1" />
                      <span>{post.author}</span>
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      <span>{post.readTime}</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Newsletter CTA */}
      <div className="py-20 bg-gradient-to-r from-[#4ECFBF]/10 to-[#3a9e92]/10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold text-gray-800 mb-6">Stay Updated</h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Get the latest language learning tips, research insights, and platform updates delivered to your inbox.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#4ECFBF] focus:border-transparent"
              />
              <button className="px-6 py-3 bg-[#4ECFBF] hover:bg-[#3a9e92] text-white font-medium rounded-lg transition-colors duration-300">
                Subscribe
              </button>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default Blog;

'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, User, Clock, ArrowRight, BookOpen, Zap, Globe, Brain, Mic, Target, ExternalLink } from 'lucide-react';

const Blog: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState("All");

  const featuredPost = {
    title: "The Future of Real-Time Voice AI: How OpenAI's Latest Models Are Revolutionizing Language Learning",
    excerpt: "Discover how cutting-edge speech-to-speech technology and conversational AI are transforming language education, making practice more natural and effective than ever before.",
    author: "Ali Pala",
    date: "January 12, 2025",
    readTime: "7 min read",
    category: "Voice AI",
    link: "https://openai.com/index/introducing-our-next-generation-audio-models/",
    icon: Mic
  };

  const posts = [
    {
      title: "Claude Opus 4: What the System Card Tells Us About Its Abilities and Risks",
      excerpt: "Deep dive into the latest AI model's capabilities and how advanced reasoning models are changing the landscape of language tutoring and personalized education.",
      author: "Ali Pala",
      date: "January 10, 2025",
      readTime: "6 min read",
      category: "AI Models",
      icon: Brain,
      link: "https://artofai.hashnode.dev/claude-opus-4-what-the-system-card-tells-us-about-its-abilities-and-risks"
    },
    {
      title: "How EmotionPrompt Revolutionizes LLM Performance in Language Learning",
      excerpt: "Exploring how emotional intelligence in AI prompts can dramatically improve language learning outcomes and create more engaging educational experiences.",
      author: "Ali Pala",
      date: "January 8, 2025",
      readTime: "5 min read",
      category: "Prompt Engineering",
      icon: Target,
      link: "https://artofai.hashnode.dev/how-emotionprompt-revolutionizes-llm-performance"
    },
    {
      title: "Understanding Reasoning in Large Language Models",
      excerpt: "Why reasoning capabilities in LLMs matter for language education and how they enable more sophisticated tutoring experiences.",
      author: "Ali Pala",
      date: "January 5, 2025",
      readTime: "8 min read",
      category: "AI Research",
      icon: BookOpen,
      link: "https://artofai.hashnode.dev/understanding-reasoning-in-large-language-models"
    },
    {
      title: "Moravec's Paradox: The Fascinating Divide Between Human and AI Intelligence",
      excerpt: "What this paradox reveals about language learning and why human-AI collaboration is the future of education technology.",
      author: "Ali Pala",
      date: "January 3, 2025",
      readTime: "6 min read",
      category: "AI Philosophy",
      icon: Zap,
      link: "https://artofai.hashnode.dev/moravecs-paradox-the-fascinating-divide-between-human-and-artificial-intelligence"
    },
    {
      title: "All You Need About MCP (Model Context Protocol)",
      excerpt: "Understanding the Model Context Protocol and its implications for building more sophisticated AI language tutoring systems.",
      author: "Ali Pala",
      date: "December 30, 2024",
      readTime: "7 min read",
      category: "AI Infrastructure",
      icon: Globe,
      link: "https://artofai.hashnode.dev/all-you-need-about-mcp"
    },
    {
      title: "AI Voice Agents in 2025: The Rise of Conversational Language Learning",
      excerpt: "How voice agents are becoming the primary interface for language practice, enabling natural conversations that adapt to learners' needs in real-time.",
      author: "Gamze Dede Pala",
      date: "December 28, 2024",
      readTime: "6 min read",
      category: "Voice AI",
      icon: Mic,
      link: "https://a16z.com/ai-voice-agents-2025-update/"
    },
    {
      title: "Personalized Learning Revolution: How AI Adapts to Every Language Learner",
      excerpt: "The shift from one-size-fits-all education to AI-powered personalized learning paths that understand individual learning styles and preferences.",
      author: "MyTaco AI Research Team",
      date: "December 25, 2024",
      readTime: "5 min read",
      category: "Personalized Learning",
      icon: Target,
      link: "https://elearningindustry.com/ai-in-education-personalized-learning-platforms"
    },
    {
      title: "The $207 Billion AI Education Market: Trends Shaping Language Learning",
      excerpt: "Market insights into the explosive growth of AI in education and what it means for the future of language learning platforms.",
      author: "MyTaco AI Research Team",
      date: "December 22, 2024",
      readTime: "4 min read",
      category: "Market Trends",
      icon: Zap,
      link: "https://www.techtarget.com/searchenterpriseai/feature/The-future-of-generative-AI-Trends-to-follow"
    },
    {
      title: "Speech-to-Speech AI: Breaking the Language Barrier in Real-Time",
      excerpt: "How the latest advances in speech-to-speech technology are enabling seamless real-time translation and conversation practice for language learners.",
      author: "MyTaco AI Research Team",
      date: "December 20, 2024",
      readTime: "6 min read",
      category: "Translation Tech",
      icon: Globe,
      link: "https://cartesia.ai/blog/state-of-voice-ai-2024"
    }
  ];

  const categories = ["All", "Voice AI", "AI Models", "Personalized Learning", "Market Trends", "AI Research", "Translation Tech", "AI Infrastructure", "Prompt Engineering", "AI Philosophy"];

  const handlePostClick = (link: string) => {
    window.open(link, '_blank', 'noopener,noreferrer');
  };

  const filteredPosts = selectedCategory === "All"
    ? posts
    : posts.filter(post => post.category === selectedCategory);

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0A0A0F' }}>
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-[#4ECFBF]/20 to-[#3a9e92]/20 border-b border-white/[0.08] py-20">
        <div className="max-w-6xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold text-white mb-6">MyTaco AI Blog</h1>
            <p className="text-xl text-white/60 max-w-3xl mx-auto leading-relaxed">
              Insights from the cutting edge of AI-powered language learning. Explore the latest trends in
              generative AI, voice technology, and personalized education from our expert team.
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
            className="rounded-2xl overflow-hidden border border-white/[0.10] cursor-pointer hover:border-[#4ECFBF]/30 transition-all duration-300"
            style={{ backgroundColor: '#13131F' }}
            onClick={() => handlePostClick(featuredPost.link)}
          >
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="bg-gradient-to-br from-[#4ECFBF]/20 to-[#3a9e92]/20 p-12 flex items-center justify-center">
                <featuredPost.icon className="w-32 h-32 text-[#4ECFBF]" />
              </div>
              <div className="p-8 lg:p-12 flex flex-col justify-center">
                <div className="flex items-center mb-4">
                  <span className="px-3 py-1 bg-[#4ECFBF]/10 text-[#4ECFBF] border border-[#4ECFBF]/20 rounded-full text-sm font-medium">
                    {featuredPost.category}
                  </span>
                  <span className="ml-2 text-white/40 text-sm">Featured</span>
                </div>
                <h2 className="text-3xl font-bold text-white mb-4">{featuredPost.title}</h2>
                <p className="text-white/60 leading-relaxed mb-6">{featuredPost.excerpt}</p>
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-white/40 text-sm">
                    <User className="w-4 h-4 mr-2" />
                    <span className="mr-4">{featuredPost.author}</span>
                    <Calendar className="w-4 h-4 mr-2" />
                    <span className="mr-4">{featuredPost.date}</span>
                    <Clock className="w-4 h-4 mr-2" />
                    <span>{featuredPost.readTime}</span>
                  </div>
                  <div className="flex items-center text-[#4ECFBF] hover:text-white font-medium transition-colors duration-200">
                    Read More <ExternalLink className="w-4 h-4 ml-2" />
                  </div>
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
                onClick={() => setSelectedCategory(category)}
                className={`px-6 py-2 rounded-full font-medium transition-all duration-300 ${
                  selectedCategory === category
                    ? "bg-[#4ECFBF] text-white"
                    : "text-white/60 hover:text-[#4ECFBF] border border-white/[0.10] hover:border-[#4ECFBF]/40"
                }`}
                style={selectedCategory !== category ? { backgroundColor: '#13131F' } : {}}
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
            {filteredPosts.map((post, index) => (
              <motion.div
                key={post.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: 0.1 * (index + 3) }}
                className="rounded-2xl border border-white/[0.10] overflow-hidden hover:border-[#4ECFBF]/30 transition-all duration-300 cursor-pointer group"
                style={{ backgroundColor: '#13131F' }}
                onClick={() => handlePostClick(post.link)}
              >
                <div className="bg-gradient-to-br from-[#4ECFBF]/10 to-[#3a9e92]/10 p-8 flex items-center justify-center group-hover:from-[#4ECFBF]/20 group-hover:to-[#3a9e92]/20 transition-all duration-300">
                  <post.icon className="w-16 h-16 text-[#4ECFBF] group-hover:scale-110 transition-transform duration-300" />
                </div>
                <div className="p-6">
                  <div className="flex items-center mb-3">
                    <span className="px-3 py-1 bg-[#4ECFBF]/10 text-[#4ECFBF] border border-[#4ECFBF]/20 rounded-full text-sm font-medium">
                      {post.category}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3 group-hover:text-[#4ECFBF] transition-colors duration-300">
                    {post.title}
                  </h3>
                  <p className="text-white/60 leading-relaxed mb-4">{post.excerpt}</p>
                  <div className="flex items-center justify-between text-white/40 text-sm">
                    <div className="flex items-center">
                      <User className="w-4 h-4 mr-1" />
                      <span>{post.author}</span>
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-1" />
                      <span>{post.readTime}</span>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center text-[#4ECFBF] opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    <span className="text-sm font-medium">Read Article</span>
                    <ExternalLink className="w-3 h-3 ml-1" />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* No posts message */}
          {filteredPosts.length === 0 && (
            <div className="text-center py-12">
              <p className="text-white/40 text-lg">No posts found in this category.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Blog;

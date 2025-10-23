import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Image, Sparkles, Info } from 'lucide-react';

export default function ChatBot() {
  const starter = "Hey there! Ready to learn something cool today? Ask me anything!";
  const [messages, setMessages] = useState([{ role: 'assistant', content: starter, images: [] }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [subject, setSubject] = useState('english');
  const [chapter, setChapter] = useState([]);
  const messagesEndRef = useRef(null);
  const [showChapters, setShowChapters] = useState(true);
  const [useCustomPrompt, setUseCustomPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedModel, setSelectedModel] = useState('azure/gpt-4o-mini');
  const [showModelInfo, setShowModelInfo] = useState(false);
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState(false);

  const models = {
    'azure/gpt-4o-mini': {
      name: 'GPT-4o Mini (Azure)',
      contextWindow: '128k tokens', 
      inputCost: '$0.15 / 1M tokens',           
      outputCost: '$0.60 / 1M tokens',          
      costPer: 'per 1M tokens',
      description: 'Cost efficient multitmodal model with vision support and large context window'
    },
    'llama-3.1-8b-instant': {
      name: 'Llama 3.1 8B Instant',
      contextWindow: '128k tokens',
      inputCost: '$0.05',
      outputCost: '$0.08',
      costPer: 'per 1M tokens',
      description: 'Fast and efficient for general tasks'
    },
    'openai/gpt-oss-20b': {
      name: 'GPT OSS 20B',
      contextWindow: '128k tokens',
      inputCost: '$0.59',
      outputCost: '$0.79',
      costPer: 'per 1M tokens',
      description: 'Balanced performance and cost'
    },
    'qwen/qwen3-32b': {
      name: 'Qwen3 32B',
      contextWindow: '131k tokens',
      inputCost: '$0.35',
      outputCost: '$0.40',
      costPer: 'per 1M tokens',
      description: 'High quality reasoning'
    },
  };

  useEffect(() => {
    sendMessage('clear')
    initialMessage(subject)
  }, [subject]);

  const local = false;
  const API_URL = local ? 'http://localhost:8100' : 'https://schooldigitalised.cogniwide.com/api/sd';

  const initialMessage = async (subject) => {
    const response = await fetch(`${API_URL}/tutor/get-initial-response/${subject}`);
    const data = await response.json();
    setMessages(prev => [...prev, { role: 'assistant', content: data?.response }]);
    console.log(data?.data);
    if (subject === 'english' && Array.isArray(data?.data)) {
      const grouped = Object.values(
        data.data.reduce((acc, item) => {
          if (!acc[item.Unit_Name]) {
            acc[item.Unit_Name] = {
              unit: item.Unit_Name,
              chapters: [],
            };
          }
          acc[item.Unit_Name].chapters.push({
            title: item.Lesson_Name,
            grammarTopics: item.Grammar_Topics || [],
          });
          return acc;
        }, {})
      );
      setChapter(grouped);
    } else {
      setChapter(data?.data || []);
    }
  }

  // Generate or retrieve session_id
  const [sessionId] = useState(() => {
    let existing = typeof window !== 'undefined' ? Math.random().toString(36).substr(2, 9) : 'demo';
    return existing;
  });

  // Scroll to bottom
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  function convertFractionsToMathML(htmlString) {
    htmlString = htmlString.replace(/(\d+)\s*\/\s*(\d+)/g, (_, num, den) => {
      return `<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">
                <mfrac><mn>${num}</mn><mn>${den}</mn></mfrac>
              </math>`;
    });

    // Convert division expressions like "4 ÷ 4 = 1"
    htmlString = htmlString.replace(/(\d+)\s*÷\s*(\d+)\s*=\s*(\d+)/g, (_, a, b, result) => {
      return `<math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">
                <mn>${a}</mn><mo>÷</mo><mn>${b}</mn><mo>=</mo><mn>${result}</mn>
              </math>`;
    });

    return htmlString;
  }

  // Send message to backend
  const sendMessage = async (text) => {
    const messageText = (typeof text === 'string' && text.trim()) ? text.trim() : input.trim();
    if (!messageText || isLoading) return;

    // Hide chapters if user clicked
    setShowChapters(false);
    setMessages(prev =>
      prev.map(msg => msg.role === 'assistant' ? { ...msg, quick_replies: [] } : msg)
    );
    setMessages(prev => [...prev, { role: 'user', content: messageText, images: [] }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(API_URL + '/tutor/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question: messageText,
          subject: subject,
          prompt: prompt,
          model: selectedModel,
          custom_prompt: useCustomPrompt? customPrompt : null,
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || 'Network error');
      }

      const data = await res.json();
      console.log(data);

      const images = Array.isArray(data.images) ? data.images : [];
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: convertFractionsToMathML(data.response.replace(/<\/?strong>/g, '')
          .replace(
            /<hint>\s*(.*?)\s*<\/hint>/gs,
            `<div style="background-color:#e6f3ff; padding:8px; border-radius:8px; font-style: italic;">$1</div>`
          ).replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')),
        images: images,
        type: data.correct_answer,
        quick_replies: Array.isArray(data.quick_replies) ? data.quick_replies : []
      }]);

      console.log(data.type);

      if (data.type === 'cleared') {
        setMessages([{ role: 'assistant', content: starter, images: [] }]);
        setShowChapters(true); // reset for new session
      }
    } catch (err) {
      console.error('Send error', err);
      setMessages(prev => [...prev, { role: 'assistant', content: 'Oops — could not reach the server. Try again.', images: [] }]);
    } finally {
      setIsLoading(false);
    }
  };

  function PromptEditor() {
    const defaultPrompt = `# Math Coach for 7th Grade
      
You are an insightful Maths Coach for 7th-grade students.

## Goal
Help students understand math concepts, Don't give direct answers.

Note: Consider 0 and 1 as numbers not as boolean values.

##Teaching Flow
  1. Warm-Up (Build Comfort & Context)
  Greet the student warmly and create a friendly learning atmosphere.
  Ask a simple, confidence-boosting question related to the topic to gauge their comfort level.

  2. Diagnose Understanding
  Ask one or two short questions to check what the student already knows.
  Listen carefully to how they think or what steps they mention.

  3. Identify the Struggle
  Encourage the student to explain what part they find confusing.

  4. Guided Discovery (Socratic Style)
  Never jump straight to the answer.
  Instead, ask guiding questions that lead the student step-by-step to figure it out.
  Use hints, analogies, and relatable examples from real life.

  5. Practice Together
  Give a similar, easy problem and let the student try solving it.
  Offer subtle hints if they get stuck, but let them do the reasoning.

  6. Reflect & Connect
  Praise their effort ("Nice work! You figured it out 🎉").
  Give a fun fact or real-world connection to make it interesting.

  7. Check Mastery
  Ask them to explain the concept in their own words to ensure true understanding.

  8. Closure
  Summarize the key takeaway in simple terms.
  Ask a reflection question to encourage self-awareness.

Example: "What part did you find easiest today, and what part should we practice again?"

##Rules
 1. Always think and respond like a real, supportive teacher.
 2. Don't reveal the final answer unless it's basic arithmetic.
 3. Use clear, simple language suitable for a 7th-grade CBSE student.
 4. Treat 0 and 1 as numbers, not as boolean values.
 5. Keep the tone friendly, encouraging, and curious.
 6. Always end a teaching interaction by checking if the student feels ready for the next challenge.
 7. Explain the concepts as explaining to a 7th grade student in Indian CBSE Board School.
 8. Already covered classes and topics:
      What topics comprise the syllabus for Class 1 maths in CBSE 2025-26? Some important topics for Class 1 Maths Syllabus 2025-26 include counting, shapes, addition, subtraction, multiplication, data handling and money. All these concepts set a foundation for more complex topics as the child grows up.
      What topics comprise the syllabus for Class 2 maths in CBSE 2025-26? Some important topics for Class 2 Maths Syllabus 2025–26 include counting in groups, 2D and 3D shapes, numbers up to 100, orientations of lines, addition and subtraction, measurement of length, weight, and capacity, multiplication and division, measurement of time, money, and data handling. All these topics help children strengthen their understanding of basic mathematical operations and logical thinking, preparing them for more advanced concepts in higher classes.
      What topics comprise the syllabus for Class 3 maths in CBSE 2025-26? The CBSE Class 3 Maths Syllabus for 2025-26 comprises fourteen chapters , which include foundational topics such as place value (What's in a Name?, House of Hundreds - I & II) , addition and subtraction (Toy Joy, Double Century, Give and Take) , simple division (Raksha Bandhan, Fair Share) , 2D shapes (Fun with Shapes) , and concepts of time and measurement (Vacation with My Nani Maa, Filling and Lifting, Time Goes On). These chapters use engaging, story-based themes like 'The Surajkund Fair' and 'Fun at Class Party!' to introduce mathematical concepts
      What topics comprise the syllabus for Class 4 maths in CBSE 2025-26? The CBSE Class 4 Maths Syllabus for 2025-26 includes fourteen units , covering topics such as geometry and patterns (Shapes Around Us , Hide and Seek , Pattern Around Us , Fun with Symmetry ), large numbers and place value (Thousands Around Us ), division and grouping (Sharing and Measuring , Equal Groups ), measurement of length, weight, and volume (Measuring Length , The Cleanest Village , Weigh it, Pour it ), concepts of time (Ticking Clocks and Turning Calendar ), and the basics of data handling (Data Handling ). The syllabus also integrates math with real-world scenarios in chapters like 'Elephants, Tigers, and Leopards' and 'The Transport Museum'
      What topics comprise the syllabus for Class 5 maths in CBSE 2025-26? The CBSE Class 5 Maths Syllabus for 2025-26 includes fifteen units that cover advanced foundational concepts like Fractions and Angles as Turns, alongside extensive real-world applications of measurement including distance and travel (We the Travellers-I & II, Far and Near), weight and capacity (Weight and Capacity, The Dairy Farm, Coconut Farm), and time (Racing Seconds). The syllabus also reinforces geometry and patterns (Shapes and Patterns, Symmetrical Designs), and culminates with lessons on data handling (Data Through Pictures).
      What topics comprise the syllabus for Class 6 maths in CBSE 2025-26? The CBSE Class 6 Maths Syllabus for 2025-26 is divided into ten core chapters , which introduce key secondary-level mathematical concepts such as Integers (The Other Side of Zero) and operations with Fractions. The syllabus also focuses on Number Theory (Number Play, Prime Time) covering HCF, LCM, and factorisation; Geometry and Mensuration (Lines and Angles, Perimeter and Area, Playing with Constructions) including basic constructions and area formulas; and Data Handling and Presentation. These concepts are strengthened with lessons on Patterns in Mathematics and Symmetry.
      Keep explanations simple, friendly, and interactive.

- Keep explanations simple, friendly, and interactive.
- Ask **one question at a time**.
- Be patient, encouraging, and adapt to the student's response.
- **Never repeat the same question.**
- Use human-readable equations (e.g., "2x + 3 = 7") not in LATEX.
- Only use the provided CONTEXT (learning materials).
  - If the answer is not in the CONTEXT, reply: "Hmm, I don't see that in what I have — could you rephrase or give more detail?"
- For conceptual or multi-step problems:
  - Respond **step-by-step**, never giving full solutions immediately.
  - If the student answers incorrectly or says "I don't know":
    <hint>
    [give a hint related to the last question]
    </hint>
- Once the student understands:
  - Praise them warmly, e.g., "Great job!"
  - Ask: "Would you like to explore this topic more, or ask a different question?"
- After giving the final answer, ask the student if they want to explore more, else close the conversation.
- When explaining math problems, always provide step-by-step solutions with examples. The example should be in a hint tag: <hint>Example: [example]</hint>.
- After asking a question, if the student answers incorrectly, correct them gracefully with an example.

##IMPORTANT RULE:
  -If the CONTEXT contains a images/ or diagrams reference like:
    ![](images/image_name.jpg)
  -You must convert it into the following HTML image format and include it in the answer:
    <img src='http://127.0.0.1:8100/app/tutor_assistant/output/images/<image_name>.jpg'>
  -Do this for each image reference found. Do not omit them. Always include converted image references in the final HTML output.

CONTEXT: {context}
 
## Response Format
\`\`\`json
{{
  "answer": "[Your response in html format]",
  "correct_answer": true/false, make it true only user answers correctly then reset it for follow up question.
  "quick_replies": [Example: 'I understand', 'I don\\'t know','Explain it more','Give me an example','Hinglish mein samjha dijiye'] max it should be 6.
}}
\`\`\`

## Answer Format
- The "answer" field must be a string in html format.
- Use html for structure:
  - Use \`<b></b>\` for emphasis.
  - Use paragraphs by having double line breaks.
- Use the \`<hint>\` tag for hints and examples, but the content inside the tag should be in html.
Example of a hint in html:
\`\`\`
<hint>
**Example:** To solve 2x + 3 = 7, first subtract 3 from both sides to get 2x = 4.
</hint>
\`\`\`

Remember: You are a math coach for 7th graders. Make it engaging and clear!`;

    const [localPrompt, setLocalPrompt] = useState(customPrompt || defaultPrompt);

    const handleSave = () => {
      setCustomPrompt(localPrompt);
      setUseCustomPrompt(true);
      setOpen(false);
    };

    return (
      <div
        className={`fixed top-0 right-0 w-full md:w-[600px] min-h-[80%] bg-gray-100 z-40 transition-transform duration-500 shadow-2xl border-l border-gray-200
          ${open ? 'translate-x-0' : 'translate-x-full'}
        `}
      >
        <div className="flex justify-between items-center p-4 border-b border-gray-300 bg-white">
          <h2 className="text-lg font-semibold text-gray-700">Math Coach Prompt</h2>
          <button
            onClick={() => setOpen(false)}
            className="text-gray-500 hover:text-gray-800 transition-colors text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="p-4">
          <textarea
            value={localPrompt}
            onChange={(e) => setLocalPrompt(e.target.value)}
            className="w-full h-[70vh] p-4 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none text-sm bg-white shadow-inner text-black"
          />
        </div>

        <div className="flex justify-end gap-3 p-4 border-t border-gray-300 bg-white">
          <button
            onClick={() => setOpen(false)}
            className="px-4 py-2 bg-gray-200 rounded-lg text-gray-700 hover:bg-gray-300"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-purple-600 rounded-lg text-white hover:bg-purple-700 shadow"
          >
            Save & Use
          </button>
        </div>
      </div>
    );
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim()) sendMessage();
    }
  };

  return (
    <div className="h-screen w-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex flex-col overflow-hidden">
      {/* Header with gradient and glow effect */}
      <div className="relative bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-5 text-white shadow-xl">
        <div className="absolute inset-0 bg-black opacity-10"></div>
        <div className="relative flex items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="absolute inset-0 bg-white rounded-full blur-md opacity-40 animate-pulse"></div>
              <div className="relative bg-white/20 backdrop-blur-sm p-3 rounded-full border-2 border-white/30">
                <Sparkles className="w-6 h-6" />
              </div>
            </div>
            <div>
              <h2 className="text-xl font-bold tracking-wide flex items-center gap-2">
                Student AI Tutor
              </h2>
              <p className="text-sm text-white/90 font-light">Your personal learning assistant</p>
            </div>
          </div>

          {/* Subject Dropdown in Header */}
          <div className="flex items-center gap-2">
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-all duration-300 shadow-lg hover:bg-white/30 text-sm font-medium cursor-pointer"
            >
              <option value="english" className="bg-purple-600 text-white">English</option>
              <option value="maths" className="bg-purple-600 text-white">Mathematics</option>
            </select>

            <label className="flex items-center gap-2 px-3 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 text-sm cursor-pointer hover:bg-white/30 transition-all duration-300">
              <input
                type="checkbox"
                checked={prompt}
                onChange={(e) => setPrompt(!prompt)}
                className="w-4 h-4 cursor-pointer"
              />
              <span>Use Custom Prompt</span>
            </label>

            <button
              onClick={() => sendMessage('clear')}
              className="px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-white border-2 border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-white/50 transition-all duration-300 shadow-lg hover:bg-white/30 text-sm font-medium cursor-pointer"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Prompt Sidebar */}
      <PromptEditor />

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col gap-2 animate-slideIn ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {/* Avatar with glow */}
              <div className="relative flex-shrink-0">
                <div className={`absolute inset-0 rounded-full blur-lg opacity-20 ${msg.role === 'user' ? 'bg-blue-400' : 'bg-purple-400'}`}></div>
                <div className={`relative w-11 h-11 rounded-full flex items-center justify-center shadow-lg transform transition-all duration-300 hover:scale-110 ${msg.role === 'user' ? 'bg-gradient-to-br from-blue-500 to-cyan-500' : 'bg-gradient-to-br from-purple-500 to-pink-500'}`}>
                  {msg.role === 'user' ? (
                    <User className="w-6 h-6 text-white" />
                  ) : (
                    <Sparkles className="w-6 h-6 text-white" />
                  )}
                </div>
              </div>

              {/* Message Bubble with enhanced styling */}
              <div className={`relative group ${msg.role === 'user' ? 'ml-auto' : 'mr-auto'}`}>
                {/* Glow effect on hover */}
                <div className={`absolute inset-0 rounded-3xl blur-2xl opacity-0 group-hover:opacity-30 transition-opacity duration-300 ${msg.role === 'user' ? 'bg-blue-100' : msg.type == true ? 'bg-yellow-100' : 'bg-purple-100'}`}></div>

                {/* Achievement style for answers */}
                {msg.role === 'assistant' && msg.type == true && (
                  <>
                    <div className="absolute -top-2 -left-2 w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg animate-bounce-slow z-10">
                      <span className="text-2xl">🏆</span>
                    </div>
                    <div className="absolute -top-1 -right-1 w-8 h-8 bg-gradient-to-br from-yellow-300 to-yellow-500 rounded-full flex items-center justify-center shadow-md z-10">
                      <span className="text-lg">✨</span>
                    </div>
                  </>
                )}

                <div className={`relative rounded-3xl px-6 py-4 shadow-lg backdrop-blur-lg transition-all duration-300 group-hover:shadow-2xl
                  ${msg.role === 'user'
                    ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white border border-white/20'
                    : msg.type === true
                      ? 'bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 text-gray-800 border-2 border-yellow-300 shadow-xl'
                      : 'bg-white/90 text-gray-800 border border-purple-100'
                  }`}
                >
                  {/* Type label with badge style */}
                  {msg.type === true && (
                    <div className={`inline-block mb-2 px-3 py-1 rounded-full text-xs font-medium ${msg.role === 'user'
                        ? 'bg-white/20 text-white'
                        : msg.type == true
                          ? 'bg-gradient-to-r from-yellow-400 to-orange-400 text-white shadow-md'
                          : 'bg-purple-100 text-purple-700'
                      }`}>
                      {msg.type === true ? '🎓 ' + 'success' : ''}
                    </div>
                  )}

                  {/* Message content */}
                  <div
                    className="whitespace-pre-wrap break-words leading-relaxed text-sm sm:text-base"
                    dangerouslySetInnerHTML={{ __html: msg.content }}
                  />
                </div>
              </div>
            </div>
            {/* Quick replies (per message) */}
            <div className={`flex gap-3 max-w-[85%] lg:ml-34 xl:ml-44 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              {msg.quick_replies && msg.quick_replies.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.quick_replies.map((reply, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(reply)}
                      className="px-4 py-1.5 bg-purple-200 text-purple-800 rounded-full hover:bg-purple-300 transition-all text-sm font-medium"
                    >
                      {reply}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        <div className="max-w-7xl mx-auto space-y-6">
          {showChapters && Array.isArray(chapter) && (
            <>
              {/* Case 1: Flat list (Maths chapters) */}
              {chapter.every(item => 'title' in item && !('chapters' in item)) ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {chapter.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => sendMessage(item.title)}
                      className="px-4 py-2 bg-pink-100 from-purple-100 to-pink-500 text-purple-800 font-medium rounded-full shadow-md hover:shadow-lg hover:from-purple-500 hover:to-pink-600 transition-all duration-300"
                    >
                      {item.title}
                    </button>
                  ))}
                </div>
              ) : (
                // Case 2: English-style grouped by unit
                chapter.map((unit, unitIdx) => (
                  <div
                    key={unitIdx}
                    className="mb-8 bg-gradient-to-r from-purple-50 to-pink-50 p-5 rounded-2xl shadow-inner"
                  >
                    <h3 className="text-xl font-bold text-purple-800 mb-4 border-b-2 border-purple-300 pb-2">
                      {unit.unit}
                    </h3>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                      {unit.chapters.map((item, idx) => (
                        <div
                          onClick={() => sendMessage(unit.unit + " : " + item.title + "\n" + 'Grammer topics' + "\n" + item.grammarTopics.join(", ")).replace(/,/g, ', ')}
                          key={idx}
                          className="cursor-pointer p-4 bg-white/80 backdrop-blur-sm rounded-xl shadow-sm hover:shadow-md hover:bg-gradient-to-br from-purple-100 to-pink-100 transition-all duration-300"
                        >
                          <button
                            className="w-full text-left font-semibold text-purple-700 hover:text-pink-700 transition-colors bg-pink-200"
                          >
                            {item.title}
                          </button>

                          {/* Grammar Topics */}
                          <small className=" text-blue-500 px-3 py-1">Grammer topics</small>
                          {item.grammarTopics && item.grammarTopics.length > 0 && (
                            <ul className="mt-2 text-sm text-gray-700 list-disc pl-5 space-y-1">
                              {item.grammarTopics.map((topic, tIdx) => (
                                <li
                                  key={tIdx}
                                  className="hover:text-pink-600 transition-colors"
                                >
                                  {topic}
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </>
          )}
        </div>

        {/* Loading indicator with enhanced animation */}
        {isLoading && (
          <div className="flex gap-3 items-start animate-slideIn">
            <div className="relative flex-shrink-0">
              <div className="absolute inset-0 rounded-full blur-lg bg-purple-400 opacity-50"></div>
              <div className="relative w-11 h-11 rounded-full flex items-center justify-center bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg">
                <Sparkles className="w-6 h-6 text-white animate-pulse" />
              </div>
            </div>
            <div className="bg-white/90 backdrop-blur-sm rounded-3xl px-6 py-4 shadow-lg border border-purple-100">
              <div className="flex gap-1.5">
                <span className="w-2.5 h-2.5 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-bounce"></span>
                <span className="w-2.5 h-2.5 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></span>
                <span className="w-2.5 h-2.5 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
        
      </div>

     
  
     
      {/* Enhanced Input Area with Model Selection */}
      <div className="relative p-4 bg-white/80 backdrop-blur-xl border-t border-purple-100 shadow-2xl">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-50 to-pink-50 opacity-50"></div>
        <div className="relative space-y-3">
          {/* Model Selection Row */}
          <div className="flex items-center gap-2 px-1">
            <label className="text-xs font-medium text-gray-600 whitespace-nowrap">AI Model:</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="flex-1 px-3 py-1.5 text-xs rounded-lg bg-white border border-purple-200 text-gray-700 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all duration-300 shadow-sm hover:shadow-md cursor-pointer"
            >
              <option value="llama-3.1-8b-instant">Llama 3.1 8B Instant (128k)</option>
              <option value="openai/gpt-oss-20b">GPT OSS 20B (128k)</option>
              <option value="qwen/qwen3-32b">Qwen3 32B (131k)</option>
              <option value="azure/gpt-4o-mini">GPT-4o-mini</option>
            </select>
            
            
            {/* Info Button */}
            <div className="relative">
              <button
                onClick={() => setShowModelInfo(!showModelInfo)}
                className="p-1.5 rounded-lg bg-purple-100 text-purple-600 hover:bg-purple-200 transition-all duration-300 shadow-sm hover:shadow-md"
                title="Model Information"
              >
                <Info className="w-4 h-4" />
              </button>
              
              {/* Info Popup */}
              {showModelInfo && (
                <div className="absolute bottom-full right-0 mb-2 w-80 bg-white rounded-xl shadow-2xl border-2 border-purple-200 p-4 z-50 animate-slideIn">
                  <button
                    onClick={() => setShowModelInfo(false)}
                    className="absolute top-2 right-2 text-gray-400 hover:text-gray-600 text-xl leading-none w-6 h-6 flex items-center justify-center"
                  >
                    ×
                  </button>
                  <h4 className="font-bold text-purple-700 mb-3 pr-6 text-sm">{models[selectedModel].name}</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between py-1.5 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Context Window:</span>
                      <span className="font-semibold text-purple-600">{models[selectedModel].contextWindow}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Input Cost:</span>
                      <span className="font-semibold text-green-600">{models[selectedModel].inputCost}</span>
                    </div>
                    <div className="flex justify-between py-1.5 border-b border-gray-100">
                      <span className="text-gray-600 font-medium">Output Cost:</span>
                      <span className="font-semibold text-green-600">{models[selectedModel].outputCost}</span>
                    </div>
                    <div className="pt-1 pb-1">
                      <span className="text-gray-500 italic">{models[selectedModel].costPer}</span>
                    </div>
                    <div className="pt-2 border-t border-gray-100">
                      <p className="text-gray-600">{models[selectedModel].description}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

              <button className='text-xs' onClick={() => setOpen(!open)}>Change prompt</button>

          </div>
                  
        


          {/* Input Row */}
          <div className="flex gap-2">
            <div className="flex-1 relative group">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-20 transition-opacity duration-300"></div>
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask me anything..."
                disabled={isLoading}
                rows={1}
                className="relative w-full px-5 py-3 text-sm rounded-2xl bg-white text-gray-800 border-2 border-purple-200 focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent resize-none transition-all duration-300 shadow-md hover:shadow-lg placeholder-gray-400"
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || isLoading}
              className="relative group bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-1 rounded-2xl hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center transition-all duration-300 shadow-lg hover:shadow-xl disabled:hover:shadow-lg transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="absolute inset-0 bg-white rounded-2xl blur-lg opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
              <Send className="relative w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Enhanced Animations */}
      <style>{`
        @keyframes slideIn {
          from { 
            opacity: 0; 
            transform: translateY(20px) scale(0.95);
          }
          to { 
            opacity: 1; 
            transform: translateY(0) scale(1);
          }
        }
        .animate-slideIn { 
          animation: slideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-5px); }
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
          width: 8px;
        }
        ::-webkit-scrollbar-track {
          background: rgba(139, 92, 246, 0.1);
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb {
          background: linear-gradient(to bottom, #a78bfa, #ec4899);
          border-radius: 10px;
        }
        ::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(to bottom, #8b5cf6, #db2777);
        }
      `}</style>
    </div>
  );
}
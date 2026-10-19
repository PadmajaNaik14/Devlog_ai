import {

  Monitor,

  Server,

  Brain,

  Database

} from "lucide-react";

const stacks = [

  {

    title: "Frontend",

    icon: Monitor,

    color: "bg-blue-100",

    iconColor: "text-blue-600",

    technologies: [

      "Next.js",

      "React",

      "TypeScript",

      "Tailwind CSS",

      "Axios"

    ]

  },

  {

    title: "Backend",

    icon: Server,

    color: "bg-green-100",

    iconColor: "text-green-600",

    technologies: [

      "Python",

      "FastAPI",

      "JWT",

      "REST APIs"

    ]

  },

  {

    title: "AI & RAG",

    icon: Brain,

    color: "bg-purple-100",

    iconColor: "text-purple-600",

    technologies: [

      "Gemini 2.5 Flash",

      "RAG",

      "Semantic Search",

      "Context Retrieval"

    ]

  },

  {

    title: "Database",

    icon: Database,

    color: "bg-orange-100",

    iconColor: "text-orange-600",

    technologies: [

      "MongoDB",

      "ChromaDB",

      "Vector Search"

    ]

  }

];

export default function TechStackSection() {

  return (

    <div
  id="tech"
  className="
  bg-white
  rounded-3xl
  shadow-xl
  border
  border-gray-100
  p-8
  h-full
  "
>

      <div className="max-w-7xl mx-auto px-8">

        <p className="text-center text-[#89023E] font-semibold">

          Technology Stack

        </p>

        <h2

          className="

          text-5xl

          font-bold

          text-center

          mt-3

          "

        >

          Built Using Modern Technologies

        </h2>

        <p

          className="

          text-center

          text-gray-500

          mt-5

          max-w-3xl

          mx-auto

          "

        >

          DevLog AI combines a modern frontend,

          scalable backend, AI technologies,

          and vector databases to provide

          an intelligent journaling experience.

        </p>

        <div

          className="

          grid

          md:grid-cols-2

          lg:grid-cols-4

          gap-8

          mt-16

          "

        >

          {

            stacks.map(

              (

                stack,

                index

              ) => {

                const Icon = stack.icon;

                return (

                  <div

                    key={index}

                    className="

                    bg-gray-50

                    rounded-3xl

                    border

                    border-gray-200

                    shadow-md

                    p-8

                    hover:-translate-y-2

                    hover:shadow-xl

                    transition-all

                    duration-300

                    "

                  >

                    <div

                      className={`

                      w-14

                      h-14

                      rounded-2xl

                      flex

                      items-center

                      justify-center

                      ${stack.color}

                      `}

                    >

                      <Icon

                        size={28}

                        className={stack.iconColor}

                      />

                    </div>

                    <h3

                      className="

                      text-2xl

                      font-bold

                      mt-6

                      mb-5

                      "

                    >

                      {stack.title}

                    </h3>

                    <ul className="space-y-3">

                      {

                        stack.technologies.map(

                          (

                            tech,

                            i

                          ) => (

                            <li

                              key={i}

                              className="

                              flex

                              items-center

                              gap-2

                              text-gray-600

                              "

                            >

                              <span className="text-green-500">

                                ✓

                              </span>

                              {tech}

                            </li>

                          )

                        )

                      }

                    </ul>

                  </div>

                );

              }

            )

          }

        </div>

      </div>

    </div>

  );

}

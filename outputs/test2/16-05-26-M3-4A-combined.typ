#set page(paper: "a4", margin: (x: 1.5cm, top: 2.5cm, bottom: 1.5cm))
#set text(font: "Roboto", size: 14pt)
#set par(leading: 0.5em)

#show: doc => {
  set page(
    header: context {
      if calc.rem(counter(page).get().first() - 1, 4) == 0 {
        place(top + left, dy: 0cm)[
          grid(
            columns: (1fr, 2fr, 1fr),
            align: (left + bottom, center + bottom, right + bottom),
            image("/images/ACT.png", height: 1.25cm),
            text(size: 18pt, weight: "bold")[Mathayom Program],
            image("/images/cambridge.png", height: 2.2cm),
          )
          line(length: 100%, stroke: 1.0pt)
        ]
      }
    },
  )
  doc
}

#align(center, text(size: 16pt, weight: "bold")[Writing Accuracy Feedback Report])
#align(center, text(size: 11pt)[Pun - 29689 - M3-4A])

#v(1em)

*Dear Pun,*

#v(0.5em)

Your suggestion to include a variety of snacks and drinks for the party was a very clear and thoughtful idea.

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. *Problems with singular and plural nouns (R:NOUN:NUM):* using a singular noun when you mean more than one. For example, you wrote "with our friend". It is better to write "with our friends".
2. *Missing verb (M:VERB):* forgetting to include the verb "is" to connect the subject and adjective. For example, you wrote "it good to celebrate". It is better to write "it is good to celebrate".
3. *Problems with prepositions (R:PREP):* using the wrong word to show time or location. For example, you wrote "on the end of year". It is better to write "at the end of the year".

#v(1em)

#align(center)[
  #text(size: 11pt)[The solid line in the chart below shows the B1 target error rate (12%). Your goal is to keep your error rate below this line. The chart tracks your progress over time.]
]

#v(0.5em)

#align(center)[
  #image("/outputs/charts/29689.png", width: 80%)
]

#v(1em)

#pagebreak()

#align(center, text(size: 16pt, weight: "bold")[Your Writing with Corrections])
#align(center, text(size: 11pt)[We scanned your writing for errors and underlined the corrections. Carefully comparing the original and corrected versions will help you become more aware of common mistakes and improve your writing skills.])

#v(0.5em)

Great #underline[idea,] it #underline[is] good to celebrate with our #underline[friends] #underline[at] the end of #underline[the] year. We could either have a party in the #underline[classroom;] it #underline[is] easy to clean #underline[up.] #underline[Then] #underline[my friends and] #underline[I] will prefer some #underline[snacks] and #underline[drinks] #underline[for] the party. We will watch #underline[a] movie or #underline[a] show during the #underline[party,] then after that #underline[we] will #underline[do] some #underline[activities] like #underline[board] #underline[games] or chess. My friend will #underline[order] some KFC and pizza #underline[for] the #underline[party.] We also have a #underline[dessert] like ice cream #underline[or] #underline[pancakes.]

#box(width: 0pt, height: 0pt) <pad-anchor-0>
#context {
  let num = counter(page).at(label("pad-anchor-0")).first()
  let gap = calc.rem-euclid(4 - num, 4)
  for _ in range(gap) {
    pagebreak()
  }
}

#pagebreak()

#align(center, text(size: 16pt, weight: "bold")[Writing Accuracy Feedback Report])
#align(center, text(size: 11pt)[Dragon - 29720 - M3-4A])

#v(1em)

*Dear Dragon,*

#v(0.5em)

Your explanation of why the classroom is a better venue than the park was very clear and persuasive.

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. *Problems with verb form (R:VERB:FORM):* using an infinitive instead of a gerund after a suggestion. For example, you wrote "suggest to play". It is better to write "suggest playing".
2. *Spelling or capitalisation mistakes (R:SPELL):* misspelling a specific brand or word. For example, you wrote "roblay". It is better to write "Roblox".
3. *Capitalisation and spacing errors (R:ORTH):* using a capital letter in the middle of a sentence. For example, you wrote "because It's". It is better to write "because it's".

#v(1em)

#align(center)[
  #text(size: 11pt)[The solid line in the chart below shows the B1 target error rate (12%). Your goal is to keep your error rate below this line. The chart tracks your progress over time.]
]

#v(0.5em)

#align(center)[
  #image("/outputs/charts/29720.png", width: 80%)
]

#v(1em)

#pagebreak()

#align(center, text(size: 16pt, weight: "bold")[Your Writing with Corrections])
#align(center, text(size: 11pt)[We scanned your writing for errors and underlined the corrections. Carefully comparing the original and corrected versions will help you become more aware of common mistakes and improve your writing skills.])

#v(0.5em)

#underline[It's] really great to hear that we're having a party! I've been waiting for #underline[this.]  \
In my opinion, I would prefer having a party in the classroom because #underline[it's] private and there would be so many people at the park. So I rather have a party in the classroom. \
For activities and games, I suggest #underline[playing] #underline[roblox,] #underline[watching] a horror movie or maybe dancing because everyone loves those. Including me, also I went to watch a movie with my friends. It's fun and we enjoyed #underline[it,] so that's the reason I suggested those #underline[activities.]  \
For food and drinks, I really recommend pizza and #underline[McDonald's] for food because It tastes very delicious and #underline[they] are my favourite. For drinks, I'd love to have #underline[Pepsi,] water and cola just because #underline[they're] refreshing. \
Reply #underline[soon!]  \
Dragon

#box(width: 0pt, height: 0pt) <pad-anchor-1>
#context {
  let num = counter(page).at(label("pad-anchor-1")).first()
  let gap = calc.rem-euclid(4 - num, 4)
  for _ in range(gap) {
    pagebreak()
  }
}

#pagebreak()

#align(center, text(size: 16pt, weight: "bold")[Writing Accuracy Feedback Report])
#align(center, text(size: 11pt)[Atom - 35309 - M3-4A])

#v(1em)

*Dear Atom,*

#v(0.5em)

I really liked how you clearly explained the reason for staying indoors by mentioning the PM 2.5 air quality.

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. *Capitalisation and spacing errors (R:ORTH):* you missed a space between words. For example, you wrote "ofcourse". It is better to write "of course".
2. *Spelling or capitalisation mistakes (R:SPELL):* you misspelled a common word. For example, you wrote "marshmellow". It is better to write "marshmallows".
3. *Problems with subject-verb agreement (R:VERB:SVA):* the verb does not match the subject. For example, you wrote "tries to speak". It is better to write "try to speak".

#v(1em)

#align(center)[
  #text(size: 11pt)[The solid line in the chart below shows the B1 target error rate (12%). Your goal is to keep your error rate below this line. The chart tracks your progress over time.]
]

#v(0.5em)

#align(center)[
  #image("/outputs/charts/35309.png", width: 80%)
]

#v(1em)

#pagebreak()

#align(center, text(size: 16pt, weight: "bold")[Your Writing with Corrections])
#align(center, text(size: 11pt)[We scanned your writing for errors and underlined the corrections. Carefully comparing the original and corrected versions will help you become more aware of common mistakes and improve your writing skills.])

#v(0.5em)

Dear Mrs Lake, \
I'm so excited for our end of year party. \
I suppose we should stay and have fun in the room. Due to the PM 2.5, partying outside is not ideal even in the park. \
I suggest that we should keep it simple and fun, and #underline[indoor-safe of course.]  \
Maybe like stuff bunny? a game where we stuff #underline[marshmallows] in our #underline[mouths,] and #underline[try] to speak. It'll be fun! \
The class #underline[has] been craving #underline[pizza!] I could order, there is one restaurant my cousin #underline[works] in. \
See you soon! \
Atom

#box(width: 0pt, height: 0pt) <pad-anchor-2>
#context {
  let num = counter(page).at(label("pad-anchor-2")).first()
  let gap = calc.rem-euclid(4 - num, 4)
  for _ in range(gap) {
    pagebreak()
  }
}

#set page(paper: "a4", margin: (x: 1.5cm, top: 2.5cm, bottom: 1.5cm))
#set text(font: "Roboto", size: 11pt)
#set par(leading: 0.4em)

#show: doc => {
  set page(
    header: context {
      if counter(page).get().first() == 1 {
        grid(
          columns: (1fr, 2fr, 1fr),
          align: (left + horizon, center + horizon, right + horizon),
          image("/images/ACT.png", height: 1.2cm),
          text(size: 14pt, weight: "bold")[Mathayom Program],
          image("/images/cambridge.png", height: 1.2cm),
        )
        line(length: 100%, stroke: 1.5pt)
      }
    },
  )
  doc
}

#align(center, text(size: 13pt, weight: "bold")[Writing Feedback Report])

#v(1em)

*Dear Atom,*

#v(0.5em)

Hi Atom,

I really liked how you used "suppose" and "suggest" to clearly express your ideas about the party!

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. R:SPELL � Check that you�re adding punctuation after greetings (like "Dear Mrs. Lake"). For example, you wrote "Dear Mrs Lake".
2. R:ORTH � Remember to add a space between words when using contractions. For example, you wrote "of course" (but it should be "of course").
3. R:VERB:SVA � When you�re making a suggestion, use the base form of the verb (not "should"). For example, you wrote "we should" (but it should be "we should").

#v(1em)
#align(center)[
  #image("/outputs/charts/35309.png", width: 80%)
]

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Your Writing])

#v(0.5em)

Dear #underline[Mrs.] Lake, \
I'm so excited for our end of year party. \
I suppose we should stay and have fun in the room. Due to the PM 2.5, partying outside is not ideal even in the park. \
I suggest that we should keep it simple and fun, and #underline[indoor-safe of course.] \
Maybe like stuff bunny? a game where we stuff #underline[marshmallows] in our mouth, and #underline[try] to speak. It'll be fun! \
The class #underline[has] been craving for #underline[pizza!] I could #underline[order;] there is one restaurant my cousin #underline[works] in. \
See you soon! \
Atom

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Corrected Writing])

#v(0.5em)

Dear Mrs. Lake,
I'm so excited for our end of year party.
I suppose we should stay and have fun in the room. Due to the PM 2.5, partying outside is not ideal even in the park.
I suggest that we should keep it simple and fun, and indoor-safe of course.
Maybe like stuff bunny? a game where we stuff marshmallows in our mouth, and try to speak. It'll be fun!
The class has been craving for pizza! I could order; there is one restaurant my cousin works in.
See you soon!
Atom

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Error Details])

#v(0.5em)
Error rate: 10%  (class: M3-4A)

#v(0.5em)
#table(
  columns: (1fr, 1fr, 2fr),
  stroke: 0.5pt,
  table.header([*Type*], [*Count*], [*Example*]),
    [R:ORTH], [3], [indoor-safe ofcourse. -> indoor-safe of course.],
    [R:VERB:SVA], [3], [tries -> try],
    [R:NOUN], [1], [Mrs -> Mrs.],
    [R:SPELL], [1], [marshmellow -> marshmallows],
    [U:PUNCT], [1], [],

)
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

*Dear Pun,*

#v(0.5em)

Hi Pun,

I liked how you used "celebrate" and "prefer" in your writing � those are great words to describe an event with friends!

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. R:NOUN: You forgot to add an "s" to "friend" when talking about a group. For example, you wrote "with our friend" (should be "friends").
2. R:PREP: "On" is not the best word to use before "the end of year." It should be "at" (e.g. "at the end of the year").
3. R:NOUN:NUM: "Snack" should have an "s" at the end because you're talking about more than one. For example, you wrote "some of Snack" (should be "snacks").

#v(1em)
#align(center)[
  #image("/outputs/charts/29689.png", width: 80%)
]

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Your Writing])

#v(0.5em)

Great #underline[idea,] it #underline[is] good to celebrate with our friend #underline[at] the end of #underline[the] year. We could either have a party in the #underline[classroom;] it #underline[is] easy to clean #underline[up,] then #underline[my friends and]#underline[I] will prefer some #underline[snacks] and #underline[drinks]#underline[for] the party. We will watch the movie or the show during the #underline[party,] then after that #underline[we] will #underline[do] some #underline[activities] like #underline[board]#underline[games] or chess. My friend will #underline[order] some KFC and pizza #underline[for] the #underline[party.] We also have a #underline[dessert] like ice cream#underline[and]#underline[pancakes.]

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Corrected Writing])

#v(0.5em)

Great idea, it is good to celebrate with our friends at the end of the year. We could either have a party in the classroom; it is easy to clean up, then my friends and I will prefer some snacks and drinks for the party. We will watch the movie or the show during the party, then after that we will do some activities like board games or chess. My friends will order some KFC and pizza for the party. We also have a dessert like ice cream and pancakes.

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Error Details])

#v(0.5em)
Error rate: 32%  (class: M3-4A)

#v(0.5em)
#table(
  columns: (1fr, 1fr, 2fr),
  stroke: 0.5pt,
  table.header([*Type*], [*Count*], [*Example*]),
    [R:NOUN], [5], [idea -> idea,],
    [M:VERB], [3], [is],
    [R:PREP], [3], [on -> at],
    [R:NOUN:NUM], [3], [Snack -> snacks],
    [R:ORTH], [2], [up -> up,],
    [U:PREP], [2], [],
    [R:SPELL], [2], [broad -> board],
    [M:DET], [1], [the],

)
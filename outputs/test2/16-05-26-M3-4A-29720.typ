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

*Dear Dragon,*

#v(0.5em)

Hi Dragon,

I really liked how you used "in my opinion" to express your personal preference clearly.

I could mostly understand what you were saying, but your communication and grade will improve a lot if you pay special attention to the following mistakes:

1. R:ORTH � You need to add punctuation at the end of sentences. For example, you wrote "In my opinion, I would prefer having a party in the classroom because It's private and there would be so many people a".
2. R:SPELL � You need to capitalize the pronoun "I" at the beginning of a sentence. For example, you wrote "It's private".
3. R:WO � You need to rearrange words in a sentence for it to make sense. For example, you wrote "also I".

#v(1em)
#align(center)[
  #image("/outputs/charts/29720.png", width: 80%)
]

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Your Writing])

#v(0.5em)

That's really great to hear that we're having a party! I've been waiting for #underline[this.] \
In my opinion, I would prefer having a party in the classroom because #underline[it's] private and there would be so many people at the park. So #underline[I'd] rather have a party in the classroom. \
For activities and games, I suggest #underline[playing] roblay, #underline[watching] a horror movie or maybe dancing because everyone loves those. Including me, #underline[I also] went to watch a movie with my friends. It's fun and we enjoyed it so that's the reason I suggested those #underline[activities.] \
For food and drinks, I really recommend pizza and #underline[McDonald's] for food because #underline[it] tastes very delicious and #underline[they] are my #underline[favorite.] For drinks, I'd love to have pepsi, water and cola just because #underline[it's refreshing.] \
Reply #underline[soon!] \
Dragon

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Corrected Writing])

#v(0.5em)

That's really great to hear that we're having a party! I've been waiting for this.
In my opinion, I would prefer having a party in the classroom because it's private and there would be so many people at the park. So I'd rather have a party in the classroom.
For activities and games, I suggest playing roblay, watching a horror movie or maybe dancing because everyone loves those. Including me, I also went to watch a movie with my friends. It's fun and we enjoyed it so that's the reason I suggested those activities.
For food and drinks, I really recommend pizza and McDonald's for food because it tastes very delicious and they are my favorite. For drinks, I'd love to have pepsi, water and cola just because it's refreshing.
Reply soon!
Dragon

#pagebreak()

#align(center, text(size: 13pt, weight: "bold")[Error Details])

#v(0.5em)
Error rate: 10%  (class: M3-4A)

#v(0.5em)
#table(
  columns: (1fr, 1fr, 2fr),
  stroke: 0.5pt,
  table.header([*Type*], [*Count*], [*Example*]),
    [R:ORTH], [5], [this -> this.],
    [R:VERB:FORM], [2], [to play -> playing],
    [R:SPELL], [2], [mcdonald -> McDonald's],
    [OTHER], [1], [I -> I'd],
    [R:WO], [1], [also I -> I also],
    [R:NOUN], [1], [activities -> activities.],
    [R:PRON], [1], [there -> they],
    [U:PUNCT], [1], [],

)
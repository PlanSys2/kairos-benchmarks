(define (domain keys-of)
  (:requirements :typing :object-fluents :negative-preconditions)
  (:types robot room door key)
  (:predicates (joins ?d - door ?a ?b - room) (open ?d - door))
  (:functions (in ?r - robot) - room (holding ?r - robot) - key (key-at ?k - key) - room
              (opens ?d - door) - key)
  (:action unlock
    :parameters (?r - robot ?d - door ?a ?b - room)
    :precondition (and (= (in ?r) ?a) (joins ?d ?a ?b) (= (holding ?r) (opens ?d))
                       (not (open ?d)))
    :effect (open ?d))
  (:action go
    :parameters (?r - robot ?d - door ?a ?b - room)
    :precondition (and (= (in ?r) ?a) (joins ?d ?a ?b) (open ?d))
    :effect (assign (in ?r) ?b))
  (:action take
    :parameters (?r - robot ?k - key ?a - room)
    :precondition (and (= (in ?r) ?a) (= (key-at ?k) ?a))
    :effect (and (assign (key-at ?k) undefined) (assign (holding ?r) ?k)))
  (:action put
    :parameters (?r - robot ?k - key ?a - room)
    :precondition (and (= (in ?r) ?a) (= (holding ?r) ?k))
    :effect (and (assign (holding ?r) undefined) (assign (key-at ?k) ?a))))

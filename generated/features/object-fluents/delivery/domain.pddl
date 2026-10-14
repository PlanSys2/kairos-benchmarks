(define (domain delivery-of)
  (:requirements :typing :object-fluents :negative-preconditions)
  (:types robot location package)
  (:predicates (connected ?a ?b - location))
  (:functions (loc ?r - robot) - location (pos ?p - package) - location
              (carrying ?r - robot) - package)
  (:action move
    :parameters (?r - robot ?from ?to - location)
    :precondition (and (= (loc ?r) ?from) (connected ?from ?to))
    :effect (assign (loc ?r) ?to))
  (:action pick
    :parameters (?r - robot ?p - package ?l - location)
    :precondition (and (= (loc ?r) ?l) (= (pos ?p) ?l) (not (= (carrying ?r) ?p)))
    :effect (and (assign (carrying ?r) ?p) (assign (pos ?p) undefined)))
  (:action drop
    :parameters (?r - robot ?p - package ?l - location)
    :precondition (and (= (loc ?r) ?l) (= (carrying ?r) ?p))
    :effect (and (assign (carrying ?r) undefined) (assign (pos ?p) ?l))))

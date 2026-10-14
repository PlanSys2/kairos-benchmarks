(define (domain elevator-of)
  (:requirements :typing :object-fluents :negative-preconditions)
  (:types elevator floor passenger)
  (:predicates (above ?a ?b - floor) (served ?p - passenger) (serves ?e - elevator ?f - floor))
  (:functions (floor-of ?e - elevator) - floor (dest ?p - passenger) - floor
              (waiting ?p - passenger) - floor (inside ?p - passenger) - elevator)
  (:action up
    :parameters (?e - elevator ?from ?to - floor)
    :precondition (and (= (floor-of ?e) ?from) (above ?to ?from) (serves ?e ?to))
    :effect (assign (floor-of ?e) ?to))
  (:action down
    :parameters (?e - elevator ?from ?to - floor)
    :precondition (and (= (floor-of ?e) ?from) (above ?from ?to) (serves ?e ?to))
    :effect (assign (floor-of ?e) ?to))
  (:action board
    :parameters (?p - passenger ?e - elevator ?f - floor)
    :precondition (and (= (floor-of ?e) ?f) (= (waiting ?p) ?f))
    :effect (and (assign (waiting ?p) undefined) (assign (inside ?p) ?e)))
  (:action leave
    :parameters (?p - passenger ?e - elevator ?f - floor)
    :precondition (and (= (floor-of ?e) ?f) (= (inside ?p) ?e) (= (dest ?p) ?f))
    :effect (and (assign (inside ?p) undefined) (served ?p))))

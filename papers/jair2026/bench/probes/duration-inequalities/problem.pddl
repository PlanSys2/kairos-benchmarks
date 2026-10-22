(define (problem di1) (:domain di) (:objects r1 - robot) (:init (ready r1) (= (charge r1) 0))
 (:goal (and (charged r1) (>= (charge r1) 4) (<= (charge r1) 6))))

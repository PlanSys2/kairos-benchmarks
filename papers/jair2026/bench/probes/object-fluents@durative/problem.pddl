(define (problem of1) (:domain of) (:objects r1 - robot a b - place)
 (:init (= (loc r1) a) (link a b) (link b b)) (:goal (and (arrived r1))))

# tests/UnsupportedTests.cmake
# ----------------------------------------------------------------------------
# The tests of PaykanLang's frontend suites (paykan_add_frontend_tests) that
# the bison frontend cannot pass, because their programs use a feature it
# leaves out (README, "Generics and `mov` are not supported").  tests/
# CMakeLists.txt filters them out of ParserTests.bison and SemaTests.bison
# with GTEST_FILTER: paykan_add_frontend_tests has no exclusion option.
#
# The lists were made from the tests that fail without them; each one's
# programs use the feature it is listed under.  The programs themselves are
# C++ string literals, so they are not run here; the samples that use the
# same features are checked by UnsupportedSamples.
# ----------------------------------------------------------------------------

# Parser suite, generics.  GrammarEdge.GenericCallInsideArgumentListStillParses:
# bison reads `f(a < b, c > (d))` as two comparisons, recursive descent as
# the generic call `a<b, c>(d)`.  GrammarEdge.NestingLimitIsTheSameOnEveryFrontend
# nests a generic type; scripts/nesting_limit.py (NestingLimit) checks its
# other constructs.
set(PAYKAN_BISON_GENERICS_PARSER_TESTS
    Conversion.GenericClassesAreUnaffected
    Generics.ArrayOfInstantiationAndInstantiationOfArray
    Generics.ExplicitCallTypeArgs
    Generics.ExplicitCallTypeArgsMultipleAndQualified
    Generics.ExplicitCtorTypeArgsNested
    Generics.GenericClassDecl
    Generics.GenericClassMultipleParamsAndSuperclass
    Generics.GenericFuncDecl
    Generics.NestedAndMultipleTypeArgs
    Generics.QualifiedGenericTypeParses
    Generics.RelationalAgainstGenericCall
    Generics.TupleAndOptionalTypeArgsOnCalls
    Generics.TypeArgsInParamsReturnFieldsAndMatchArms
    Generics.TypeArgsInVariableAnnotation
    GrammarEdge.CommonErrorsAreLocatedAlike
    GrammarEdge.GenericCallInsideArgumentListStillParses
    GrammarEdge.NestingLimitIsTheSameOnEveryFrontend
)

# Parser suite, mov.
set(PAYKAN_BISON_MOV_PARSER_TESTS
    Mov.MoveInReturn
    Mov.MoveString
    Mov.MoveTemporaryCall
    Mov.MoveVariable
)

# Sema suite, generics.
set(PAYKAN_BISON_GENERICS_SEMA_TESTS
    Conversion.GenericCallsAreStillGenericCalls
    Conversion.InferredFormInsideGenericsAndCalls
    Func.IllTypedMainIsOneErrorAtItsDeclaration
    Generics.ArityErrorOnCall
    Generics.ArityErrorOnType
    Generics.BoxIntNotAssignableToBoxStr
    Generics.ConstructorArgumentInference
    Generics.DuplicateTypeParam
    Generics.ErrorInsideFunctionInstantiationNamesIt
    Generics.ErrorInsideInstantiationNamesIt
    Generics.ExportedInstantiationIsUsableAsConcreteClass
    Generics.GenericClassUsedWithoutTypeArgs
    Generics.GenericClassWithConcreteSuperclass
    Generics.ImportedTemplateReportedOncePerUse
    Generics.ImportedTemplatesAreRejected
    Generics.InferenceAmbiguous
    Generics.InferenceFailsWithoutArguments
    Generics.InferenceFromEmptyArrayLiteralFails
    Generics.InferenceFromPlainArrayAndBoxParams
    Generics.InstantiationAsFieldParamReturnAndArray
    Generics.InstantiationDepthGuard
    Generics.InstantiationsAreInjectedIntoTU
    Generics.MatchOnInstantiationArms
    Generics.MovOfInstantiation
    Generics.RecursiveInstantiationInFieldIsFine
    Generics.SameInstantiationIsSameClassType
    Generics.TemplateNameCollisions
    Generics.TypeArgsOnNonGeneric
    Generics.TypeParamShadowsType
    Generics.TypeParamUsedAsValue
    Generics.UninstantiatedTemplateBodyIsNotChecked
    Generics.UnknownTemplate
    Generics.WrongConstructorArgumentNamesInstantiation
    GenericsTypes.ExportedInstantiationNamesWithCommasAndArrays
    GenericsTypes.InferenceThroughTuplesAndOptionals
    GenericsTypes.NoneAloneCannotInferOptionalParam
    GenericsTypes.OptionalOfPrimitiveArgumentIsAccepted
    GenericsTypes.TupleAndOptionalBodiesInstantiate
    GenericsTypes.TupleAndOptionalTypeArgs
    GenericsTypes.TupleArityMismatchLeftToArgumentCheck
    Module.MissingModuleUsesAreSilent
    OptionalPrimitive.GenericsInstantiateWithOptionalPrimitives
)

# Sema suite, mov.
set(PAYKAN_BISON_MOV_SEMA_TESTS
    Mov.AndMoveInLhsStaysMovedAfter
    Mov.AndMoveInLhsVisibleInRhs
    Mov.AndMoveInRhsNoLaterUseOk
    Mov.AndMoveInRhsStaysMovedAfter
    Mov.AndMoveInRhsThenRevivedOk
    Mov.AndRhsMoveDoesNotPoisonSiblingTernaryBranch
    Mov.DoubleMoveRejected
    Mov.MovNoneInsideALiteralForANonOptionalSlotIsOneError
    Mov.MovNoneInsideALiteralTakesTheElementType
    Mov.MovNoneIntoANonOptionalSlotIsOneError
    Mov.MovNoneIntoAnOptionalSlotOk
    Mov.MoveArrayElementRejected
    Mov.MoveBeforeLoopStaysMovedInsideRejected
    Mov.MoveInBranchStillMovedAfterConstruct
    Mov.MoveInLoopConditionRejected
    Mov.MoveInLoopDeclaredInsideOk
    Mov.MoveInLoopDeclaredOutsideRejected
    Mov.MoveInLoopReassignedBeforeBackEdgeOk
    Mov.MoveInLoopReassignedOnlySomePathsRejected
    Mov.MoveInMatchArmDoesNotPoisonSiblingArm
    Mov.MoveInThenDoesNotPoisonElse
    Mov.MoveMemberVariableRejected
    Mov.MoveParameterOk
    Mov.MovePrimitiveOk
    Mov.MoveRevivedInBothBranchesOk
    Mov.MoveRevivedInOnlyThenBranchRejected
    Mov.MoveSelfRejected
    Mov.MoveStringOk
    Mov.MoveTemporaryOk
    Mov.MoveThenReuseInSameCallRejected
    Mov.OrMoveInLhsVisibleInRhs
    Mov.OrMoveInRhsNoLaterUseOk
    Mov.OrMoveInRhsStaysMovedAfter
    Mov.ReassignRevivesVariable
    Mov.TernaryMoveInBothBranchesOk
    Mov.TernaryMoveInBothBranchesThenUseRejected
    Mov.TernaryMoveInConditionStaysMovedAfter
    Mov.TernaryMoveInConditionVisibleInBothBranches
    Mov.TernaryMoveInElseDoesNotPoisonThen
    Mov.TernaryMoveInElseThenUseRejected
    Mov.TernaryMoveInOneBranchThenUseRejected
    Mov.TernaryMoveInThenDoesNotPoisonElse
    Mov.TernaryMoveInsideStatementBranchIsolated
    Mov.TernaryNestedBranchesIsolated
    Mov.UseAfterMoveInExpr
    Mov.UseAfterMoveRead
    Mov.UseThenMoveInSameCallOk
    Optional.MovOfOptional
    Poison.EveryUseOfAPoisonedVariableIsSilent
    Tuple.DestructureRevivesMovedVariable
    Tuple.MovOfElementRejected
    Tuple.UseAfterMovRejected
    Tuple.WholeTupleCanBeMoved
)

# Frontend suite: the in-process differential check runs over the whole
# samples corpus with no way to skip a file; FrontendDifferential runs the
# same check through the installed paykan, skipping
# tests/unsupported_samples.txt.
set(PAYKAN_BISON_CORPUS_FRONTEND_TESTS
    Differential.EveryFrontendAgreesOnEverySample
)

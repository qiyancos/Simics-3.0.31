;;; dml-mode.el --- major mode for editing DML

;; Copyright 2006-2007 Virtutech AB

;; Code copied from font-lock.el
;; Copyright (C) 1992, 93, 94, 95, 96, 97, 98, 1999, 2000, 2001
;;  Free Software Foundation, Inc.

;; This file is NOT part of GNU Emacs.

;; This program is free software; you can redistribute it and/or
;; modify it under the terms of the GNU General Public License as
;; published by the Free Software Foundation; either version 2 of the
;; License, or (at your option) any later version.
     
;; This program is distributed in the hope that it will be useful, but
;; WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
;; General Public License for more details.
     
;; You should have received a copy of the GNU General Public License
;; along with this program; if not, write to the Free Software
;; Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111,
;; USA.

(require 'cc-mode)

;;;c-paren-re and c-identifier-re were helper macros that
;;;got removed from cc-mode, as noted in the Emacs changelog
;;;for 2002-09-10.
(defmacro c-paren-re (re)
  `(concat "\\(" ,re "\\)"))
(defmacro c-identifier-re (re)
  `(concat "\\<\\(" ,re "\\)\\>[^_]"))


(defconst c-DML-primitive-type-kwds
  "bool\\|char\\|double\\|float\\|u?int[0-9]*\\|long\\|short\\|void\\|struct\\|union\\|vect")

(defconst c-DML-specifier-kwds
  "local\\|auto\\|const\\|extern\\|static\\|signed\\|unsigned\\|volatile\\|restrict")

(defconst c-DML-class-kwds "device\\|bank\\|register\\|field\\|group\\|attribute\\|event\\|connect\\|implement\\|interface\\|method\\|parameter\\|data\\|template")

(defconst c-DML-extra-toplevel-kwds "dml\\|import\\|bitorder\\|loggroup\\|constant\\|header\\|footer")

(defconst c-DML-other-decl-kwds "enum\\|typedef")

(defconst c-DML-decl-level-kwds "is\\|size")

(defconst c-DML-block-stmt-1-kwds "do\\|else\\|in\\|where")

(defconst c-DML-block-stmt-2-kwds "for\\|foreach\\|select\\|if\\|switch\\|while\\|try")

(defconst c-DML-simple-stmt-kwds "goto\\|break\\|continue\\|return\\|throw\\|return\\|error\\|delete\\|call\\|inline\\|after\\|assert\\|log")

(defconst c-DML-label-kwds "case\\|default\\|catch")

(defconst c-DML-expr-kwds "new\\|this\\|cast\\|sizeof\\|sizeoftype\\|typeof\\|defined\\|undefined")

(defconst c-DML-reserved-future-kwds "class\\|namespace\\|private\\|protected\\|public\\|using\\|virtual")

(defconst c-DML-keywords
  (concat c-DML-primitive-type-kwds "\\|" c-DML-specifier-kwds
	  "\\|" c-DML-class-kwds "\\|" c-DML-extra-toplevel-kwds
	  "\\|" c-DML-other-decl-kwds "\\|" c-DML-decl-level-kwds
	  "\\|" c-DML-block-stmt-1-kwds "\\|" c-DML-block-stmt-2-kwds
	  "\\|" c-DML-simple-stmt-kwds "\\|" c-DML-label-kwds
	  "\\|" c-DML-expr-kwds "\\|" c-DML-reserved-future-kwds))

(defconst c-DML-class-key (c-paren-re c-DML-class-kwds))

(defconst c-DML-comment-start-regexp "//")

(defcustom dml-font-lock-extra-types '("\\sw+_t")
  "*List of extra types to fontify in DML mode.
Each list item should be a regexp not containing word-delimiters.
For example, a value of (\"FILE\" \"\\\\sw+_t\") means the word FILE and words
ending in _t are treated as type names.

The value of this variable is used when Font Lock mode is turned on."
  :type 'font-lock-extra-types-widget
  :group 'font-lock-extra-types)

(let* ((dml-objects
	(eval-when-compile
	  (regexp-opt '("device" "bank" "register" "field" "group"
                        "attribute" "event" "connect" "implement" "interface"))))
       (dml-objects-depth
        (regexp-opt-depth dml-objects))
       (dml-keywords
	(eval-when-compile
	  (regexp-opt '("break" "continue" "do" "else" "for" "foreach" "in"
                        "if" "return" "assert"
			"switch" "while" "sizeof" "sizeoftype" "defined"
                        "import" "log" "template" "data"
			"typedef" "extern" "auto" "local" "static" "const"
                        "method" "parameter" "loggroup" "constant" "is"
                        "call" "inline" "default" "throw" "try" "catch"))))
       (dml-type-specs
	(eval-when-compile
	  (regexp-opt '("enum" "struct" "union"))))
       (dml-type-specs-depth
	(regexp-opt-depth dml-type-specs))
       (dml-type-names
	`(mapconcat 'identity
	  (append
	   (list ,(eval-when-compile
                    (regexp-opt
                     '("bool" "char" "short" "int" "long" "signed" "unsigned"
                       "float" "double" "void" "complex"))))
           '("u?int[0-9]+")
	   dml-font-lock-extra-types)
	  "\\|"))
       (dml-type-names-depth
	`(regexp-opt-depth ,dml-type-names)))
 (setq dml-font-lock-keywords-1
  (list
   '("^\\s-*method\\>\\s-*\\(\\sw+\\)"
     1 'font-lock-function-name-face)
   '("^\\s-*parameter\\>\\s-*\\(\\sw+\\)"
     1 'font-lock-constant-face)
   '("^\\s-*\\<\\(template\\|is\\)\\>\\s-*\\(\\sw+\\)"
     2 'font-lock-type-face)
   '("^\\s-*\\<\\(data\\)\\>\\s-*\\(\\sw+\\)\\s-*\\(\\sw+\\)"
     1 'font-lock-type-face
     2 'font-lock-variable-name-face)
   ;;
   ;; Fontify object definitions
   (list (concat "\\<\\(" dml-objects "\\)\\>\\s-*\\(\\sw+\\)")
         (+ dml-objects-depth 2) 'font-lock-builtin-face) ;
   ;;
   ;; Fontify filenames in import
   ;;'("^import[ \t]*\\(\"[^\"\n]*\"\\)"
   ;;  1 'font-lock-string-face)
   ;;
   ;; Fontify function macro names.
   '("^\\(constant\\|loggroup\\)[ \t]+\\(\\sw+\\)" 2 'font-lock-constant-face)
   '("\\<\\(true\\|false\\|undefined\\|NULL\\)\\>" 1 'font-lock-constant-face)
   '("^dml [0-9\\.]*" 0 'font-lock-builtin-face)))

 (setq dml-font-lock-keywords-2
  (append dml-font-lock-keywords-1
   (list
    ;;
    ;; Simple regexps for speed.
    ;;
    ;; Fontify all type names.
    `(eval .
      (cons (concat "\\<\\(" ,dml-type-names "\\)\\>") 'font-lock-type-face))
    ;;
    ;; Fontify all builtin keywords (except case, default and goto; see below).
    (concat "\\<\\(" dml-objects "\\|" dml-keywords "\\|" dml-type-specs "\\)\\>")
    ;;
    ;; Fontify case/goto keywords and targets, and case default/goto tags.
    '("\\<\\(case\\|goto\\)\\>"
      (1 'font-lock-keyword-face)
      ("\\(-[0-9]+\\|\\sw+\\)"
       ;; Return limit of search.
       (save-excursion (skip-chars-forward "^:\n") (point))
       nil
       (1 'font-lock-constant-face nil t)))
    ;; Anders Lindgren <andersl@andersl.com> points out that it is quicker to
    ;; use MATCH-ANCHORED to effectively anchor the regexp on the left.
    ;; This must come after the one for keywords and targets.
    '(":" ("^[ \t]*\\(\\sw+\\)[ \t]*:[ \t]*$"
	   (beginning-of-line) (end-of-line)
	   (1 'font-lock-constant-face)))
    )))

 (setq dml-font-lock-keywords-3
  (append dml-font-lock-keywords-2
   ;;
   ;; More complicated regexps for more complete highlighting for types.
   ;; We still have to fontify type specifiers individually, as C is so hairy.
   (list
    ;;
    ;; Fontify all storage types, plus their items.
    `(eval .
      (list (concat "\\<\\(" ,dml-type-names "\\)\\>"
		    "\\([ \t*&]+\\sw+\\>\\)*")
	    ;; Fontify each declaration item.
	    (list 'font-lock-match-c-style-declaration-item-and-skip-to-next
		  ;; Start with point after all type specifiers.
		  (list 'goto-char (list 'or
					 (list 'match-beginning
					       (+ ,dml-type-names-depth 2))
					 '(match-end 1)))
		  ;; Finish with point after first type specifier.
		  '(goto-char (match-end 1))
		  ;; Fontify as a variable or function name.
		  '(1 (if (match-beginning 2)
			  'font-lock-function-name-face
			'font-lock-variable-name-face)))))
    ;;
    ;; Fontify all storage specs and types, plus their items.
    `(eval .
      (list (concat "\\<\\(" ,dml-type-specs "\\)\\>"
		    "[ \t]*\\(\\sw+\\)?")
	  (list 1 'font-lock-keyword-face)
	  (list ,(+ dml-type-specs-depth 2) 'font-lock-type-face nil t)
	  (list 'font-lock-match-c-style-declaration-item-and-skip-to-next
		  nil 
		  ;; Finish with point after the variable name if
		  ;; there is one.
		  `(if (match-end 2) 
		       (goto-char (match-end 2)))
		  ;; Fontify as a variable or function name.
		  '(1 (if (match-beginning 2)
			  'font-lock-function-name-face
			'font-lock-variable-name-face) nil t))))
    ;;
    ;; Fontify structures, or typedef names, plus their items.
    '("\\(}\\)[ \t*]*\\sw"
      (font-lock-match-c-style-declaration-item-and-skip-to-next
       (goto-char (match-end 1)) nil
       (1 'font-lock-type-face)))
    ;;
    ;; Fontify anything at beginning of line as a declaration or definition.
    '("^\\(\\sw+\\)\\>\\([ \t*]+\\sw+\\>\\)*"
      (1 'font-lock-type-face)
      (font-lock-match-c-style-declaration-item-and-skip-to-next
       (goto-char (or (match-beginning 2) (match-end 1))) nil
       (1 (if (match-beginning 2)
	      'font-lock-function-name-face
	    'font-lock-variable-name-face))))
    )))
 )

(defun dml-mode ()
  "Major mode for editing DML code.

Key bindings:
\\{c-mode-map}"
  (interactive)
  (kill-all-local-variables)
  (c-initialize-cc-mode)
  (set-syntax-table c-mode-syntax-table)

  ;; In Emacs 22, we need to send an argument to c-common-init
  (condition-case e
      (c-common-init 'c-mode)
    (wrong-number-of-arguments (c-common-init)))

  (setq major-mode 'dml-mode
	mode-name "DML"
	local-abbrev-table c-mode-abbrev-table
	abbrev-mode t)
  (use-local-map c-mode-map)
  (setq comment-start "// "
	comment-end   ""
	c-keywords (c-identifier-re c-DML-keywords)
	;c-conditional-key c-C-conditional-key
	c-class-key c-DML-class-key
	c-baseclass-key nil
	c-comment-start-regexp c-DML-comment-start-regexp
	;c-bitfield-key c-C-bitfield-key
        font-lock-defaults '((dml-font-lock-keywords
                              dml-font-lock-keywords-1
                              dml-font-lock-keywords-2
                              dml-font-lock-keywords-3)
                             nil nil ((?_ . "w") (?- . "w")) beginning-of-defun
                             (font-lock-mark-block-function . mark-defun))
	)
  (cc-imenu-init cc-imenu-c-generic-expression)
  (setq c-basic-offset 4)
  (run-hooks 'c-mode-common-hook)
  (run-hooks 'dml-mode-hook)
  (c-update-modeline))

(provide 'dml-mode)

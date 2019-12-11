/*
 * simics/util/swabber-ws32.il
 *
 * This file is part of Virtutech Simics
 *
 * Copyright (C) 1998-2005 Virtutech AB, All Rights Reserved
 *
 * The Virtutech Simics API is distributed under license. Please refer to
 * the 'LICENSE' file for details.
 *
 * For documentation on the Virtutech Simics API, please refer to the
 * Simics Reference Manual. Please report any difficulties you encounter
 * with this API through the Virtutech Simics website at www.simics.com
 *
*/

.inline loadswab32, 4
	lduwa [ %o0 ] #ASI_P_L, %o0
.end

.inline loadswab16, 4
	lduha [ %o0 ] #ASI_P_L, %o0
.end

.inline storeswab32, 8
	stwa %o1, [ %o0 ] #ASI_P_L
.end

.inline storeswab16, 6
	stha %o1, [ %o0 ] #ASI_P_L
.end
